import os
import logging
import requests
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعدادات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# TOKEN - تأكد من تغييره!
TOKEN = os.getenv("TOKEN", "8481752278:AAHs9O3Ilf0LRTJPIAhpdC92gC3_ufME78g")

# Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Bot is running! Go to Telegram and send /start"

# وظائف البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة أمر /start"""
    user = update.effective_user
    await update.message.reply_text(
        f"مرحباً {user.first_name}! 👋\n"
        f"البوت يعمل على render ✅\n\n"
        f"جرب: /test"
    )

async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اختبار طلب HTTP"""
    try:
        # اختبار requests
        response = requests.get('https://api.ipify.org?format=json', timeout=5)
        ip = response.json()['ip']
        
        await update.message.reply_text(
            f"✅ كل شيء يعمل!\n"
            f"📡 عنوان السيرفر: {ip}\n"
            f"🔧 requests: مثبت ✔️"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {str(e)}")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رد على الرسائل النصية"""
    await update.message.reply_text(f"📨 رسلت: {update.message.text}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"حدث خطأ: {context.error}")

def main():
    """الدالة الرئيسية"""
    try:
        print("🚀 بدء تشغيل البوت...")
        print(f"🔑 TOKEN: {'تم تعيينه' if TOKEN != 'YOUR_BOT_TOKEN_HERE' else 'غير معين!'}")
        
        # إنشاء التطبيق
        application = Application.builder().token(TOKEN).build()
        
        # إضافة handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("test", test))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
        application.add_error_handler(error_handler)
        
        # تشغيل البوت
        print("✅ البوت يعمل! اضغط Ctrl+C للإيقاف")
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
        
    except Exception as e:
        print(f"❌ خطأ: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
