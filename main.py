#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بوت تلجرام لاستقبال أفكار المستخدمين
مع Flask للuptime على Render
"""

import json
import os
import logging
from datetime import datetime
from threading import Thread
from flask import Flask

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# ========== إعداد Flask للuptime ==========
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 بوت تلجرام للأفكار يعمل بنجاح!", 200

@app.route('/health')
def health():
    return {"status": "online", "service": "telegram-ideas-bot"}, 200

def run_flask():
    """تشغيل Flask في thread منفصل"""
    app.run(host='0.0.0.0', port=5000)

# ========== إعدادات البوت ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8283832279:AAFUR_rAxkIiu-ZsF9YXGAuc394uHhaWZ5o")
DEVELOPER_CHAT_ID = os.environ.get("DEVELOPER_CHAT_ID","7305720183")

# ========== إعداد التسجيل ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== قاعدة البيانات البسيطة ==========
class Database:
    def __init__(self, file="ideas.json"):
        self.file = file
        if not os.path.exists(file):
            self.save({"ideas": {}, "users": {}, "last_id": 0})
    
    def load(self):
        try:
            with open(self.file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"ideas": {}, "users": {}, "last_id": 0}
    
    def save(self, data):
        with open(self.file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def add_idea(self, user_id, username, text):
        data = self.load()
        idea_id = data["last_id"] + 1
        data["last_id"] = idea_id
        
        data["ideas"][str(idea_id)] = {
            "user_id": user_id,
            "username": username or "مجهول",
            "text": text,
            "status": "pending",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "response": None
        }
        
        if str(user_id) not in data["users"]:
            data["users"][str(user_id)] = {
                "username": username,
                "submitted": 0,
                "approved": 0,
                "rejected": 0
            }
        
        data["users"][str(user_id)]["submitted"] += 1
        self.save(data)
        return idea_id
    
    def get_idea(self, idea_id):
        data = self.load()
        return data["ideas"].get(str(idea_id))
    
    def update_idea(self, idea_id, status, response=None):
        data = self.load()
        if str(idea_id) in data["ideas"]:
            idea = data["ideas"][str(idea_id)]
            old_status = idea["status"]
            idea["status"] = status
            idea["response"] = response
            
            user_id = str(idea["user_id"])
            if old_status == "pending":
                if status == "approved":
                    data["users"][user_id]["approved"] += 1
                elif status == "rejected":
                    data["users"][user_id]["rejected"] += 1
            
            self.save(data)
            return True
        return False
    
    def get_pending(self):
        data = self.load()
        return [{"id": k, **v} for k, v in data["ideas"].items() if v["status"] == "pending"]
    
    def get_user_stats(self, user_id):
        data = self.load()
        user = data["users"].get(str(user_id))
        if user:
            pending = sum(1 for idea in data["ideas"].values() 
                         if idea["user_id"] == user_id and idea["status"] == "pending")
            return {**user, "pending": pending}
        return None

db = Database()

# ========== دوال البوت ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /start"""
    text = """
🎉 **مرحباً بك في بوت الأفكار!**

هنا يمكنك إرسال أفكارك لتحسين البوت الرئيسي.

**طريقة الاستخدام:**
1. اكتب فكرتك مباشرة في الرسالة
2. أو استخدم `/idea فكرتك`
3. استخدم `/myideas` لمعرفة حالة أفكارك

**مثال:** `/idea إضافة ميزة جديدة للبحث`
    """
    await update.message.reply_text(text, parse_mode='Markdown')

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /help"""
    text = """
🆘 **المساعدة:**

✅ **لإرسال فكرة:** 
- اكتب فكرتك مباشرة
- أو استخدم `/idea فكرتك`

✅ **لمعرفة أحوال أفكارك:**
- استخدم `/myideas`

✅ **للتحدث مع المطور:**
- اكتب فكرتك وسيصلها البوت للمطور
- سيصلك رد عندما يقرر المطور
    """
    await update.message.reply_text(text, parse_mode='Markdown')

async def idea_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /idea"""
    if not context.args:
        await update.message.reply_text("⚠️ اكتب فكرتك بعد الأمر. مثال: `/idea إضافة ميزة جديدة`", parse_mode='Markdown')
        return
    
    user = update.effective_user
    idea_text = ' '.join(context.args)
    idea_id = db.add_idea(user.id, user.username or user.first_name, idea_text)
    
    await update.message.reply_text(
        f"✅ **تم استلام فكرتك!**\n\n"
        f"📝 **رقم الفكرة:** #{idea_id}\n"
        f"💡 **فكرتك:** {idea_text}\n\n"
        f"📨 سيتم مراجعتها من المطور قريباً.",
        parse_mode='Markdown'
    )
    
    await send_to_dev(idea_id, user, idea_text, context)

async def myideas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /myideas"""
    user = update.effective_user
    stats = db.get_user_stats(user.id)
    
    if not stats:
        await update.message.reply_text("📭 لم ترسل أي أفكار بعد. ابدأ بـ `/idea فكرتك`", parse_mode='Markdown')
        return
    
    text = f"""
📊 **أفكارك:**

👤 **اسمك:** @{stats['username'] or 'مجهول'}
📨 **المرسلة:** {stats['submitted']}
✅ **المقبولة:** {stats['approved']}
❌ **المرفوضة:** {stats['rejected']}
⌛ **قيد الانتظار:** {stats['pending']}
    """
    await update.message.reply_text(text, parse_mode='Markdown')

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل العادية"""
    if update.message.text.startswith('/'):
        return
    
    user = update.effective_user
    idea_text = update.message.text.strip()
    
    idea_id = db.add_idea(user.id, user.username or user.first_name, idea_text)
    
    await update.message.reply_text(
        f"✅ **تم استلام فكرتك!**\n\n"
        f"📝 **رقمها:** #{idea_id}\n"
        f"💡 **فكرتك:** {idea_text}\n\n"
        f"📨 سيتم مراجعتها من المطور.",
        parse_mode='Markdown'
    )
    
    await send_to_dev(idea_id, user, idea_text, context)

async def send_to_dev(idea_id, user, idea_text, context):
    """إرسال الفكرة للمطور"""
    try:
        dev_id = int(DEVELOPER_CHAT_ID)
    except:
        logger.error("❌ معرف المطور غير صحيح!")
        return
    
    text = f"""
🎯 **فكرة جديدة!**

📝 **الرقم:** #{idea_id}
👤 **من:** @{user.username or user.first_name}
🆔 **ID:** {user.id}
📅 **الوقت:** {db.get_idea(idea_id)['date']}
💡 **الفكرة:** 
{idea_text}
    """
    
    keyboard = [
        [InlineKeyboardButton("✅ موافق", callback_data=f"ok_{idea_id}"),
         InlineKeyboardButton("❌ رفض", callback_data=f"no_{idea_id}")],
        [InlineKeyboardButton("✍️ رد مخصص", callback_data=f"custom_{idea_id}")]
    ]
    
    try:
        await context.bot.send_message(
            chat_id=dev_id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"❌ خطأ في الإرسال: {e}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة أزرار الموافقة/الرفض"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    idea_id = int(data.split('_')[1])
    action = data.split('_')[0]
    
    idea = db.get_idea(idea_id)
    if not idea:
        await query.edit_message_text("❌ الفكرة محذوفة!")
        return
    
    if action == "ok":
        db.update_idea(idea_id, "approved", "تمت الموافقة، وسيتم التنفيذ قريباً إن شاء الله")
        new_text = query.message.text + "\n\n✅ **تمت الموافقة**"
        await query.edit_message_text(new_text, parse_mode='Markdown')
        await send_response(context, idea['user_id'], idea_id, True, "تمت الموافقة على فكرتك وسيتم البدء في تنفيذها قريباً إن شاء الله.")
    
    elif action == "no":
        response = "نعتذر، فكرتك صعبة التنفيذ حالياً أو لا تناسب خطة التطوير."
        db.update_idea(idea_id, "rejected", response)
        new_text = query.message.text + f"\n\n❌ **تم الرفض**\n📝 **السبب:** {response}"
        await query.edit_message_text(new_text, parse_mode='Markdown')
        await send_response(context, idea['user_id'], idea_id, False, response)
    
    elif action == "custom":
        context.user_data['waiting_response_for'] = idea_id
        await query.message.reply_text(f"✍️ اكتب ردك للفكرة #{idea_id}:")

async def handle_dev_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة رد المطور المخصص"""
    try:
        if update.effective_chat.id != int(DEVELOPER_CHAT_ID):
            return
    except:
        return
    
    if 'waiting_response_for' not in context.user_data:
        return
    
    idea_id = context.user_data['waiting_response_for']
    response_text = update.message.text
    
    keyboard = [
        [InlineKeyboardButton("✅ موافق بهذا الرد", callback_data=f"ok_custom_{idea_id}"),
         InlineKeyboardButton("❌ رفض بهذا الرد", callback_data=f"no_custom_{idea_id}")]
    ]
    
    await update.message.reply_text(
        f"📝 **ردك:** {response_text}\n\nاختر الإجراء:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    context.user_data[f'custom_response_{idea_id}'] = response_text

async def custom_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة أزرار الرد المخصص"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    parts = data.split('_')
    action = parts[0]
    idea_id = int(parts[2])
    
    response_text = context.user_data.get(f'custom_response_{idea_id}', "تم الرد على فكرتك.")
    
    idea = db.get_idea(idea_id)
    if not idea:
        await query.edit_message_text("❌ الفكرة محذوفة!")
        return
    
    status = "approved" if action == "ok" else "rejected"
    db.update_idea(idea_id, status, response_text)
    
    emoji = "✅" if status == "approved" else "❌"
    status_text = "مقبولة" if status == "approved" else "مرفوضة"
    
    new_text = query.message.text + f"\n\n{emoji} **{status_text}**\n💬 **الرد:** {response_text}"
    await query.edit_message_text(new_text, parse_mode='Markdown')
    
    await send_response(context, idea['user_id'], idea_id, action == "ok", response_text)
    
    # تنظيف
    for key in ['waiting_response_for', f'custom_response_{idea_id}']:
        if key in context.user_data:
            del context.user_data[key]

async def send_response(context, user_id, idea_id, approved, response):
    """إرسال رد للمستخدم"""
    emoji = "✅" if approved else "❌"
    status_text = "مقبولة" if approved else "مرفوضة"
    
    text = f"""
{emoji} **تم الرد على فكرتك #{idea_id}**

📋 **الحالة:** {status_text}
💬 **رد المطور:** 
{response}

{"🎉 سنبدأ التنفيذ قريباً!" if approved else "شكراً لمشاركتك!"}
    """
    
    try:
        await context.bot.send_message(chat_id=user_id, text=text, parse_mode='Markdown')
    except:
        try:
            await context.bot.send_message(
                chat_id=int(DEVELOPER_CHAT_ID),
                text=f"⚠️ لم أستطع إرسال الرد للمستخدم:\n\n{text}",
                parse_mode='Markdown'
            )
        except:
            pass

async def pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /pending للمطور"""
    try:
        if update.effective_chat.id != int(DEVELOPER_CHAT_ID):
            await update.message.reply_text("⛔ هذا للمطور فقط!")
            return
    except:
        await update.message.reply_text("⛔ خطأ في المعرف!")
        return
    
    pending_list = db.get_pending()
    
    if not pending_list:
        await update.message.reply_text("✅ لا توجد أفكار معلقة.")
        return
    
    text = f"📋 **الأفكار المعلقة ({len(pending_list)})**\n\n"
    for idea in pending_list:
        text += f"#{idea['id']} - 👤 @{idea['username']}\n"
        text += f"💡 {idea['text'][:60]}...\n"
        text += f"📅 {idea['date']}\n"
        text += "─\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /stats للمطور"""
    try:
        if update.effective_chat.id != int(DEVELOPER_CHAT_ID):
            return
    except:
        return
    
    data = db.load()
    total = len(data["ideas"])
    pending = len([i for i in data["ideas"].values() if i["status"] == "pending"])
    approved = len([i for i in data["ideas"].values() if i["status"] == "approved"])
    rejected = len([i for i in data["ideas"].values() if i["status"] == "rejected"])
    users = len(data["users"])
    
    text = f"""
📊 **إحصائيات البوت:**

👥 **المستخدمين:** {users}
💡 **إجمالي الأفكار:** {total}
⌛ **المعلقة:** {pending}
✅ **المقبولة:** {approved}
❌ **المرفوضة:** {rejected}
    """
    
    await update.message.reply_text(text, parse_mode='Markdown')

def main():
    """الدالة الرئيسية لتشغيل كل شيء"""
    print("🤖 بدء تشغيل بوت الأفكار مع Flask للuptime...")
    
    # التحقق من الإعدادات
    if BOT_TOKEN == "ضع_توكن_البوت_هنا":
        print("❌ لم تعدل BOT_TOKEN! اضبطه في متغيرات البيئة على Render")
        return
    
    if DEVELOPER_CHAT_ID == "ضع_معرف_المطور_هنا":
        print("❌ لم تعدل DEVELOPER_CHAT_ID! اضبطه في متغيرات البيئة على Render")
        return
    
    # تشغيل Flask في thread منفصل
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("🌐 Flask يعمل على بورت 5000 للuptime")
    
    # إنشاء وإعداد بوت تلجرام
    app = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("idea", idea_cmd))
    app.add_handler(CommandHandler("myideas", myideas))
    app.add_handler(CommandHandler("pending", pending))
    app.add_handler(CommandHandler("stats", stats))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(ok|no|custom)_[0-9]+$"))
    app.add_handler(CallbackQueryHandler(custom_button_handler, pattern="^(ok|no)_custom_[0-9]+$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_dev_response))
    
    print("🚀 بوت تلجرام جاهز للعمل!")
    print("📞 اذهب إلى @BotFather وأرسل /setcommands ثم:")
    print("""
start - بدء البوت
help - المساعدة
idea - إرسال فكرة
myideas - أفكارك
pending - الأفكار المعلقة (للمطور)
stats - الإحصائيات (للمطور)
    """)
    
    # تشغيل البوت
    app.run_polling()

if __name__ == "__main__":
    main()
