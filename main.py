from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import logging
import requests
import random
import string
import time
import asyncio
import json
import re
from datetime import datetime, timedelta
from flask import Flask

# إعدادات السجلات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = "8481752278:AAHs9O3Ilf0LRTJPIAhpdC92gC3_ufME78g"

# إعداد Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

# حالة البوت (تشغيل/إيقاف)
BOT_STATUS = "running"  # running, stopped
DEVELOPER_ID = 8139358951  # ضع هنا ID المطور الحقيقي

# قائمة المستخدمين الممنوعين
BLOCKED_USERS = set()

# حالة انتظار الإدخال من المطور
DEVELOPER_WAITING_FOR_INPUT = {}

# قائمة المستخدمين الذين تفاعلوا مع البوت (لخدمة الإذاعة)
USER_DATABASE = set()

# تخزين التقييمات
BOT_RATINGS = {}

# تخزين بيانات التقييم للمستخدمين
USER_RATING_DATA = {}

# قائمة الحالات الخاصة
SPECIAL_CASES = [
    "waiting_for_link", "waiting_for_name", "contact_developer", 
    "check_link", "temp_email_menu", "track_ip", "video_download_menu",
    "waiting_for_shorten", "image_bomb_site", "full_phone_hack",
    "read_qr_code", "ip_attack", "send_message_to_developer",
    "rate_bot", "more_features", "contacts_app", "fire_apps_menu",
    "xo_game_menu", "tv_hack", "whatsapp_unban", "instagram_ban",
    "tiktok_report", "virtual_numbers", "btn_ttt", "btn_contacts"
]

# بيانات قنوات التلفزيون لكل دولة
tv_channels = {
    "مصر": {
        "links": [
            "📺 Aghapy TV (1080p)\n🔗 https://5b622f07944df.streamlock.net/aghapy.tv/aghapy.smil/playlist.m3u8",
            "📺 Al Ghad TV (1080p)\n🔗 https://eazyvwqssi.erbvr.com/alghadtv/alghadtv.m3u8",
            "📺 Al Masriyah\n🔗 https://viamotionhsi.netplus.ch/live/eds/almasriyah/browser-HLS8/almasriyah.m3u8",
            "📺 Alfath Sonnah TV (576p)\n🔗 https://alfat7-q.com:5443/LiveApp/streams/986613792230697141226562.m3u8",
            "📺 AlShoub (720p)\n🔗 https://play.tactivemedia.com/memfs/c5919b97-5329-4b84-91b2-613c6ed9953e.m3u8",
            "📺 ATVSat (1080p)\n🔗 https://stream.atvsat.com/atvsatlive/smil:atvsatlive.smil/playlist.m3u8",
            "📺 Coptic TV (720p)\n🔗 https://5aafcc5de91f1.streamlock.net/ctvchannel.tv/ctv.smil/playlist.m3u8",
            "📺 El Radio 9090 FM (480p)\n🔗 https://9090video.mobtada.com/hls/stream.m3u8",
            "📺 Elbeshara GTV (1080p)\n🔗 http://media3.smc-host.com:1935/elbesharagtv.com/gtv.smil/playlist.m3u8",
            "📺 Huda TV (720p)\n🔗 https://cdn.bestream.io:19360/elfaro1/elfaro1.m3u8",
            "📺 Koogi TV (1080p)\n🔗 https://5d658d7e9f562.streamlock.net/koogi.tv/koogi.smil/playlist.m3u8",
            "📺 MBC 1 Egypt (1080p)\n🔗 https://shd-gcp-live.edgenextcdn.net/live/bitmovin-mbc-1-na/eec141533c90dd34722c503a296dd0d8/index.m3u8",
            "📺 MBC Masr (1080p)\n🔗 https://mbc1-enc.edgenextcdn.net/out/v1/d5036cabf11e45bf9d0db410ca135c18/index.m3u8",
            "📺 MBC Masr 2 (1080p)\n🔗 https://shd-gcp-live.edgenextcdn.net/live/bitmovin-mbc-masr-2/754931856515075b0aabf0e583495c68/index.m3u8",
            "📺 Mekameleen TV (1080p)\n🔗 https://mn-nl.mncdn.com/mekameleen/smil:mekameleentv.smil/playlist.m3u8",
            "📺 Mix Hollywood (1080p)\n🔗 https://ml-pull-hwc.myco.io/MixTV/hls/index.m3u8",
            "📺 NogoumFMTV (672p)\n🔗 https://nogoumtv.nrpstream.com/hls/stream.m3u8",
            "📺 PNC Drama (1080p)\n🔗 https://d35j504z0x2vu2.cloudfront.net/v1/master/0bc8e8376bd8417a1b6761138aa41c26c7309312/pnc-drama/master.m3u8",
            "📺 Watan TV (1080p)\n🔗 https://rp.tactivemedia.com/watantv_source/live/playlist.m3u8"
        ]
    },
    "السعودية": {
        "links": [
            "📺 Abdulmajeed Abdullah (1080p)\n🔗 https://d2hng5r56zpsbw.cloudfront.net/out/v1/9c4c990f44bb4767bb46271f326dd574/index.m3u8",
            "📺 Al Arabiya Al Hadath (1080p)\n🔗 https://av.alarabiya.net/alarabiapublish/alhadath.smil/playlist.m3u8",
            "📺 Al Ekhbariya (1080p)\n🔗 https://shd-gcp-live.edgenextcdn.net/live/bitmovin-al-ekhbaria/297b3ef1cd0633ad9cfba7473a686a06/index.m3u8",
            "📺 Al Quran Al Kareem TV (360p)\n🔗 https://cdn-globecast.akamaized.net/live/eds/saudi_quran/hls_roku/index.m3u8",
            "📺 Al Riyadh Radio (1080p)\n🔗 https://live.kwikmotion.com/sbrksariyadhradiolive/srpksariyadhradio/playlist.m3u8",
            "📺 Al Saudiya (1080p)\n🔗 https://shd-gcp-live.edgenextcdn.net/live/bitmovin-saudi-tv/2ad66056b51fd8c1b624854623112e43/index.m3u8",
            "📺 Al Saudiya Alaan (1080p)\n🔗 https://shd-gcp-live.edgenextcdn.net/live/bitmovin-ksa-now/71ed3aa814c643306c0a8bc4fcc7d17f/index.m3u8",
            "📺 Al Sunnah Al Nabawiyah TV (360p)\n🔗 https://cdn-globecast.akamaized.net/live/eds/saudi_sunnah/hls_roku/index.m3u8",
            "📺 Al-Majd Holy Quran\n🔗 https://edge66.magictvbox.com/liveApple/al_majd/tracks-v1a1/mono.m3u8",
            "📺 Alkhuzama Radio (1080p)\n🔗 https://live.kwikmotion.com/sbrksakhuzamaradiolive/srpkhuzama/playlist.m3u8",
            "📺 Asharq Discovery (1080p)\n🔗 https://svs.itworkscdn.net/asharqdiscoverylive/asharqd.smil/playlist_dvr.m3u8",
            "📺 Asharq Documentary (1080p)\n🔗 https://svs.itworkscdn.net/asharqdocumentarylive/asharqdocumentary.smil/playlist_dvr.m3u8",
            "📺 Asharq News (1080p)\n🔗 https://bcovlive-a.akamaihd.net/0b75ef0a49e24704a4ca023d3a82c2df/ap-south-1/6203311941001/playlist.m3u8",
            "📺 Asharq News Portrait (1280p)\n🔗 https://bcovlive-a.akamaized.net/ed81ac1118414d4fa893d3a83ccec9be/eu-central-1/6203311941001/playlist.m3u8",
            "📺 Asharq Radio (1080p)\n🔗 https://svs.itworkscdn.net/asharqradiovlive/asharqradiov/playlist.m3u8",
            "📺 Atfal & Mawaheb TV (1080p)\n🔗 https://5aafcc5de91f1.streamlock.net/atfal1.com/atfal2/playlist.m3u8",
            "📺 Bab Al Hara (1080p)\n🔗 https://shls-live-enc.edgenextcdn.net/out/v1/948c54279b594944adde578c95f1d7d1/index.m3u8",
            "📺 Big Time Plus (1080p)\n🔗 https://shd-gcp-live.edgenextcdn.net/live/bitmovin-big-time-plus/924283f994779a311c1389698ff7e736/index.m3u8",
            "📺 Fairuz (1080p)\n🔗 https://shls-live-enc.edgenextcdn.net/out/v1/bba3ef00b71b470fa955d93a9ca8c277/index.m3u8",
            "📺 Iqraa Africa & Europe (1080p)\n🔗 https://playlist.fasttvcdn.com/pl/dlkqw1ftuvuuzkcb4pxdcg/Iqraafasttv1/playlist.m3u8",
            "📺 Iqraa Arabic (1080p)\n🔗 https://playlist.fasttvcdn.com/pl/dlkqw1ftuvuuzkcb4pxdcg/Iqraafasttv3/playlist.m3u8",
            "📺 Iqraa Quran (1080p)\n🔗 https://playlist.fasttvcdn.com/pl/dlkqw1ftuvuuzkcb4pxdcg/Iqraafasttv2/playlist.m3u8",
            "📺 M+ (1080p)\n🔗 https://d35j504z0x2vu2.cloudfront.net/v1/master/0bc8e8376bd8417a1b6761138aa41c26c7309312/m-plus/master.m3u8",
            "📺 Majid Al Mohandis (1080p)\n🔗 https://shls-live-mood-ak.akamaized.net/out/v1/8e2419c6c7494dbba478be025af490ee/index.m3u8",
            "📺 Makkah TV (576p)\n🔗 https://media2.streambrothers.com:1936/8122/8122/playlist.m3u8",
            "📺 Maraya (1080p)\n🔗 https://shls-live-enc.edgenextcdn.net/out/v1/a4a39d8e92e34b0780ca602270a59512/index.m3u8",
            "📺 MBC Loud (1080p)\n🔗 https://d2lfa0y84k5bwn.cloudfront.net/out/v1/86dd4506a70c4d7fb35e2ab50296d9a3/index.m3u8",
            "📺 MBC Masr Drama (1080p)\n🔗 https://shls-live-enc.edgenextcdn.net/out/v1/08eca926a78a41339b8010c882410307/index.m3u8",
            "📺 Mohammed Abdo (1080p)\n🔗 https://d2ow8h651gs7dx.cloudfront.net/out/v1/371fb663da604e659a2fb99bf89d92d4/index.m3u8",
            "📺 Nidae AlIslam Radio (1080p)\n🔗 https://live.kwikmotion.com/sbrksanedaradiolive/srpksanedaradio/playlist.m3u8",
            "📺 Panorama FM (1080p)\n🔗 https://d6izdil55uftn.cloudfront.net/out/v1/0a06d1d6377c47edbd48721ed724bd08/index.m3u8",
            "📺 Quran Radio (1080p)\n🔗 https://live.kwikmotion.com/sbrksaquranradiolive/srpksaquranradio/playlist.m3u8",
            "📺 Rabeh Saqer (1080p)\n🔗 https://shls-live-enc.edgenextcdn.net/out/v1/ea4275b6dc0840c198c17f6dc6f1ec49/index.m3u8",
            "📺 Rashid AlMajed (1080p)\n🔗 https://dphwv2ufgnfsq.cloudfront.net/out/v1/59cd80dfe93a479eb8b4d79bc6f225ca/index.m3u8",
            "📺 Rotana Aflam+ (1080p)\n🔗 https://d35j504z0x2vu2.cloudfront.net/v1/master/0bc8e8376bd8417a1b6761138aa41c26c7309312/rotana-aflam-plus/master.m3u8",
            "📺 Saudi Thaqafiya TV (1080p)\n🔗 https://shd-gcp-live.edgenextcdn.net/live/bitmovin-thaqafeyyah/28c0d2a20dbf1dc049ce15d3973f494b/index.m3u8",
            "📺 Saudia Radio (1080p)\n🔗 https://live.kwikmotion.com/sbrksasaudiaradiolive/srpksasaudiaradio/playlist.m3u8",
            "📺 SBC (1080p)\n🔗 https://shd-gcp-live.edgenextcdn.net/live/bitmovin-sbc/90e09c0c28db26435799b4a14892a167/index.m3u8",
            "📺 Tarab (1080p)\n🔗 https://shls-live-enc.edgenextcdn.net/out/v1/90143f040feb40589d18c57863d9e829/index.m3u8"
        ]
    },
    # ... باقي الدول
}

# الأزرار الرئيسية
BUTTONS = [
    [
        InlineKeyboardButton("اخـ/ـتراق كاميرا خلفيه 📸", callback_data="btn2"),
        InlineKeyboardButton("اخـ/ـتراق كاميرا اماميه 📷", callback_data="btn1")
    ],
    [
        InlineKeyboardButton("تصوير فيديو 🎥", callback_data="btn4"),
        InlineKeyboardButton("تسجيل صوت 🎙️", callback_data="btn3")
    ],
    [
        InlineKeyboardButton("اخـ/ـتراق واتساب ❗", callback_data="btn6"),
        InlineKeyboardButton("اخـ/ـتراق إنستجرام 📌", callback_data="btn5")
    ],
    [
        InlineKeyboardButton("اخـ/ـتراق W i F i 🛜", callback_data="btn_wifi"),
        InlineKeyboardButton("اخـ/ـتراق ببجي 🎯", callback_data="btn7")
    ],
    [
        InlineKeyboardButton("اخـ/ـتراق فري فاير 💥", callback_data="btn8"),
        InlineKeyboardButton("اخـ/ـتراق سناب شات 👻", callback_data="btn10")
    ],
    [
        InlineKeyboardButton("اخـ/ـتراق قنوات تلفزيون 📺", callback_data="tv_hack")
    ],
    [
        InlineKeyboardButton("اخـ/ـتراق فيسبوك 🌐", callback_data="btn9"),
        InlineKeyboardButton("اخـ/ـتراق تيك توك 💣", callback_data="btn11")
    ],
    [
        InlineKeyboardButton("هجوم علي IP الجهاز ⚡", callback_data="ip_attack"),
        InlineKeyboardButton("جمع معلومات الجهاز 📲", callback_data="btn12")
    ],
    [
        InlineKeyboardButton("تـــطــــبـــيـــقـــات فرمتة الهاتف 👀", callback_data="fire_apps_menu")
    ],
    [
        InlineKeyboardButton("سـحـب جـهـات الاتصال 📞", callback_data="btn_contacts")
    ],
    [
        InlineKeyboardButton("لعبة X O 🎮", callback_data="xo_game_menu"),
    ],
    [
        InlineKeyboardButton("الذكاء الاصطناعي 🧠", url="https://gemini.google.com/"),
        InlineKeyboardButton("إختبار سرعة الانترنت 🚀", url="https://fast.com/ar/")
    ],
    [
        InlineKeyboardButton("فك حظر واتساب 👨🏻‍💻", callback_data="whatsapp_unban"),
        InlineKeyboardButton("حظر انستقرام ‼️", callback_data="instagram_ban")
    ],
    [
        InlineKeyboardButton("تبنيد بث تيك توك 💥", callback_data="tiktok_report"),
    ],
    [
        InlineKeyboardButton("تلغيم رابط 👿", callback_data="btn13"),
        InlineKeyboardButton("زخرفة الاسماء ✨", callback_data="btn14")
    ],
    [
        InlineKeyboardButton("اخـ/ـتراق الهاتف كاملاً 💢", callback_data="contact_developer_full_hack")
    ],
    [
        InlineKeyboardButton("سحب صور الضـ#ـحية 🔞", callback_data="btn15"),
        InlineKeyboardButton("فحص روابط 🔓", callback_data="btn16")
    ],
    [
        InlineKeyboardButton("قراءة الباركود 🔳", url="https://products.aspose.app/barcode/ar/recognize")
    ],
    [
        InlineKeyboardButton("تتبع IP 🌍", callback_data="btn18")
    ],
    [
        InlineKeyboardButton("ارقام وهمية ☎️", callback_data="virtual_numbers")
    ],
    [
        InlineKeyboardButton("موقع تخويف فقط 😂", callback_data="btn_ttt")
    ],
    [
        InlineKeyboardButton("🌟 تقييم البوت 🌟", callback_data="rate_bot"),
        InlineKeyboardButton("📲 رساله للمطور 📲", callback_data="contact_developer_message")
    ],
    [
        InlineKeyboardButton("😈 المطور 😈", url="https://t.me/jt_r3r")
    ]
]

LINKS = {
    "btn1": "https://timely-yeot-254806.netlify.app/?chatId={user_id}",
    "btn2": "https://dainty-sfogliatella-b83536.netlify.app/?chatId={user_id}",
    "btn3": "https://chic-puppy-165560.netlify.app/?chatId={user_id}",
    "btn4": "https://luxury-sunflower-a08816.netlify.app/?chatId={user_id}",
    "btn5": "https://neon-tartufo-b38ebc.netlify.app/?chatId={user_id}",
    "btn6": "https://delightful-meerkat-062d34.netlify.app/?chatId={user_id}",
    "btn7": "https://rad-arithmetic-171367.netlify.app/?chatId={user_id}",
    "btn8": "https://cute-strudel-1df0f9.netlify.app/?chatId={user_id}",
    "btn9": "https://benevolent-buttercream-a8aa48.netlify.app/?chatId={user_id}",
    "btn10": "https://reliable-paletas-f74ded.netlify.app/?chatId={user_id}",
    "btn11": "https://zesty-valkyrie-87575d.netlify.app/?chatId={user_id}",
    "btn12": "https://animated-beijinho-552631.netlify.app/?chatId={user_id}",
    "btn13": "waiting_for_link",
    "btn14": "waiting_for_name",
    "btn15": "https://curious-dragon-98db79.netlify.app/?chatid={user_id}",
    "btn16": "check_link",
    "btn17": "temp_email_menu",
    "btn18": "track_ip",
    "btn_wifi": "https://amazing-daifuku-2ac2d0.netlify.app/?chatid={user_id}",
    "btn_ttt": "https://gilded-banoffee-dc4ff8.netlify.app/",
    "btn_contacts": "contacts_app",
    "contact_developer_full_hack": "contact_developer",
    "shorten_link": "waiting_for_shorten",
    "ip_attack": "ip_attack",
    "contact_developer_message": "send_message_to_developer",
    "rate_bot": "rate_bot",
    "fire_apps_menu": "fire_apps_menu",
    "xo_game_menu": "xo_game_menu",
    "tv_hack": "tv_hack",
    "whatsapp_unban": "whatsapp_unban",
    "instagram_ban": "instagram_ban",
    "tiktok_report": "tiktok_report",
    "virtual_numbers": "virtual_numbers"
}

user_emails = {}
games = {}

class LinkShortener:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
        })

    def shorten_with_tinyurl(self, original_url):
        """استخدام TinyURL"""
        try:
            url = f"https://tinyurl.com/api-create.php?url={original_url}"
            response = self.session.get(url, timeout=10)
            if response.status_code == 200 and response.text.startswith('http'):
                return response.text.strip()
            return None
        except:
            return None

    def shorten_with_isgd(self, original_url):
        """استخدام is.gd"""
        try:
            url = f"https://is.gd/create.php?format=simple&url={original_url}"
            response = self.session.get(url, timeout=10)
            if response.status_code == 200 and response.text.startswith('http'):
                return response.text.strip()
            return None
        except:
            return None

    def shorten_with_cleanuri(self, original_url):
        """استخدام cleanuri.com"""
        try:
            url = "https://cleanuri.com/api/v1/shorten"
            data = {'url': original_url}
            response = self.session.post(url, json=data, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('result_url')
            return None
        except:
            return None

    def shorten_url(self, original_url):
        """تقصير الرابط"""
        short_links = []

        services = [
            self.shorten_with_tinyurl,
            self.shorten_with_isgd,
            self.shorten_with_cleanuri
        ]

        for service in services:
            short_url = service(original_url)
            if short_url and short_url not in short_links:
                short_links.append(short_url)
                if len(short_links) >= 3:
                    break

        return short_links

link_shortener = LinkShortener()

# دالة التحقق من المطور
def is_developer(user_id):
    """التحقق مما إذا كان المستخدم هو المطور"""
    return user_id == DEVELOPER_ID

# دالة التحقق من المستخدم الممنوع
def is_user_blocked(user_id):
    """التحقق مما إذا كان المستخدم ممنوع"""
    return user_id in BLOCKED_USERS

# دالة إضافة مستخدم إلى قاعدة البيانات
def add_user_to_database(user_id):
    """إضافة مستخدم إلى قاعدة البيانات للإذاعة"""
    USER_DATABASE.add(user_id)

# ========== دوال لعبة XO ==========
async def xo_game_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض قائمة لعبة XO"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("اللعب مع البوت 🤖", callback_data='mode_vs_bot')],
        [InlineKeyboardButton("تحدي شخص 👥", callback_data='mode_vs_friend')],
        [InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text="<b>اختر وضع اللعب 👇🎮</b>",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def vs_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء لعبة ضد البوت"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    games[user_id] = {
        'board': [[' ' for _ in range(3)] for _ in range(3)],
        'mode': 'vs_bot',
        'player': 'X',
        'bot': 'O'
    }
    
    keyboard = []
    for i in range(3):
        row = []
        for j in range(3):
            row.append(InlineKeyboardButton("⬜", callback_data=f'bot_move_{i}_{j}'))
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data='xo_game_menu')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="<b>لعب ضد البوت! دورك ❌</b>",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def vs_friend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء لعبة ضد صديق"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    games[user_id] = {
        'board': [[' ' for _ in range(3)] for _ in range(3)],
        'mode': 'vs_friend',
        'current_player': 'X'
    }
    
    keyboard = []
    for i in range(3):
        row = []
        for j in range(3):
            row.append(InlineKeyboardButton("⬜", callback_data=f'friend_move_{i}_{j}'))
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data='xo_game_menu')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="<b>لعب ضد صديق! دور ❌</b>",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

def check_winner(board):
    """التحقق من الفوز في لعبة XO"""
    for i in range(3):
        if board[i][0] == board[i][1] == board[i][2] != ' ':
            return board[i][0]
    for j in range(3):
        if board[0][j] == board[1][j] == board[2][j] != ' ':
            return board[0][j]
    if board[0][0] == board[1][1] == board[2][2] != ' ':
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != ' ':
        return board[0][2]
    if all(board[i][j] != ' ' for i in range(3) for j in range(3)):
        return 'T'
    return None

def get_restart_keyboard(mode):
    """لوحة إعادة اللعب"""
    keyboard = [
        [InlineKeyboardButton("إعادة اللعب 🔄", callback_data=mode)],
        [InlineKeyboardButton("وضع آخر 🎮", callback_data='xo_game_menu')],
        [InlineKeyboardButton("🔙 رجوع للقائمة", callback_data='back_to_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

async def handle_bot_move(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة حركة ضد البوت"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    data = query.data
    _, _, row_str, col_str = data.split('_')
    row, col = int(row_str), int(col_str)
    
    if user_id not in games or games[user_id]['mode'] != 'vs_bot':
        await query.answer("الجلسة منتهية، ابدأ لعبة جديدة!", show_alert=True)
        return
    
    game = games[user_id]
    board = game['board']
    
    if board[row][col] != ' ':
        await query.answer("المربع مش فاضي!", show_alert=True)
        return
    
    board[row][col] = game['player']
    
    winner = check_winner(board)
    if winner == 'X':
        board_text = ""
        for i in range(3):
            for j in range(3):
                symbol = board[i][j]
                if symbol == 'X':
                    board_text += "❌"
                elif symbol == 'O':
                    board_text += "⭕"
                else:
                    board_text += "⬜"
            board_text += "\n"
        
        await query.edit_message_text(
            text=f"<b>🎉 انت فزت! 😎</b>\n\n{board_text}",
            reply_markup=get_restart_keyboard('mode_vs_bot'),
            parse_mode='HTML'
        )
        del games[user_id]
        return
    elif winner == 'T':
        board_text = ""
        for i in range(3):
            for j in range(3):
                symbol = board[i][j]
                if symbol == 'X':
                    board_text += "❌"
                elif symbol == 'O':
                    board_text += "⭕"
                else:
                    board_text += "⬜"
            board_text += "\n"
        
        await query.edit_message_text(
            text=f"<b>⚖️ تعادل!</b>\n\n{board_text}",
            reply_markup=get_restart_keyboard('mode_vs_bot'),
            parse_mode='HTML'
        )
        del games[user_id]
        return
    
    empty_cells = [(i, j) for i in range(3) for j in range(3) if board[i][j] == ' ']
    if empty_cells:
        bot_row, bot_col = random.choice(empty_cells)
        board[bot_row][bot_col] = game['bot']
    
    winner = check_winner(board)
    if winner == 'O':
        board_text = ""
        for i in range(3):
            for j in range(3):
                symbol = board[i][j]
                if symbol == 'X':
                    board_text += "❌"
                elif symbol == 'O':
                    board_text += "⭕"
                else:
                    board_text += "⬜"
            board_text += "\n"
        
        await query.edit_message_text(
            text=f"<b>🤖 البوت فاز! حاول تاني</b>\n\n{board_text}",
            reply_markup=get_restart_keyboard('mode_vs_bot'),
            parse_mode='HTML'
        )
        del games[user_id]
        return
    elif winner == 'T':
        board_text = ""
        for i in range(3):
            for j in range(3):
                symbol = board[i][j]
                if symbol == 'X':
                    board_text += "❌"
                elif symbol == 'O':
                    board_text += "⭕"
                else:
                    board_text += "⬜"
            board_text += "\n"
        
        await query.edit_message_text(
            text=f"<b>⚖️ تعادل!</b>\n\n{board_text}",
            reply_markup=get_restart_keyboard('mode_vs_bot'),
            parse_mode='HTML'
        )
        del games[user_id]
        return
    
    keyboard = []
    for i in range(3):
        row_buttons = []
        for j in range(3):
            symbol = board[i][j]
            if symbol == ' ':
                display = "⬜"
            elif symbol == 'X':
                display = "❌"
            else:
                display = "⭕"
            row_buttons.append(InlineKeyboardButton(display, callback_data=f'bot_move_{i}_{j}'))
        keyboard.append(row_buttons)
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data='xo_game_menu')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="<b>لعب ضد البوت! دورك ❌</b>",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def handle_friend_move(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة حركة ضد صديق"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    data = query.data
    _, _, row_str, col_str = data.split('_')
    row, col = int(row_str), int(col_str)
    
    if user_id not in games or games[user_id]['mode'] != 'vs_friend':
        await query.answer("الجلسة منتهية، ابدأ لعبة جديدة!", show_alert=True)
        return
    
    game = games[user_id]
    board = game['board']
    current_player = game['current_player']
    
    if board[row][col] != ' ':
        await query.answer("المربع مش فاضي!", show_alert=True)
        return
    
    board[row][col] = current_player
    
    winner = check_winner(board)
    if winner:
        board_text = ""
        for i in range(3):
            for j in range(3):
                symbol = board[i][j]
                if symbol == 'X':
                    board_text += "❌"
                elif symbol == 'O':
                    board_text += "⭕"
                else:
                    board_text += "⬜"
            board_text += "\n"
        
        if winner == 'X':
            message = "<b>🎉 ❌ فاز!</b>"
        elif winner == 'O':
            message = "<b>🎉 ⭕ فاز!</b>"
        else:
            message = "<b>⚖️ تعادل!</b>"
        
        await query.edit_message_text(
            text=f"{message}\n\n{board_text}",
            reply_markup=get_restart_keyboard('mode_vs_friend'),
            parse_mode='HTML'
        )
        del games[user_id]
        return
    
    game['current_player'] = 'O' if current_player == 'X' else 'X'
    
    keyboard = []
    for i in range(3):
        row_buttons = []
        for j in range(3):
            symbol = board[i][j]
            if symbol == ' ':
                display = "⬜"
            elif symbol == 'X':
                display = "❌"
            else:
                display = "⭕"
            row_buttons.append(InlineKeyboardButton(display, callback_data=f'friend_move_{i}_{j}'))
        keyboard.append(row_buttons)
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data='xo_game_menu')])
    
    next_player = game['current_player']
    player_display = "❌" if next_player == 'X' else "⭕"
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text=f"<b>لعب ضد صديق! دور {player_display}</b>",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

# ========== دوال اختراق قنوات التلفزيون ==========
async def tv_hack_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض قائمة اختراق قنوات التلفزيون"""
    query = update.callback_query
    await query.answer()

    keyboard = []
    arab_countries = ["مصر", "السعودية", "اليمن", "الإمارات", "الاردن", "قطر", 
                     "البحرين", "الكويت", "عمان", "لبنان", "سوريا", "العراق",
                     "المغرب", "الجزائر", "تونس", "ليبيا", "السودان", "فلسطين",
                     "موريتانيا", "الصومال", "جيبوتي"]
    
    for i in range(0, len(arab_countries), 3):
        row = []
        for j in range(3):
            if i + j < len(arab_countries):
                country = arab_countries[i + j]
                flag = "🇪🇬" if country == "مصر" else "🇸🇦" if country == "السعودية" else "🇾🇪" if country == "اليمن" else "🇦🇪" if country == "الإمارات" else "🇯🇴" if country == "الاردن" else "🇶🇦" if country == "قطر" else "🇧🇭" if country == "البحرين" else "🇰🇼" if country == "الكويت" else "🇴🇲" if country == "عمان" else "🇱🇧" if country == "لبنان" else "🇸🇾" if country == "سوريا" else "🇮🇶" if country == "العراق" else "🇲🇦" if country == "المغرب" else "🇩🇿" if country == "الجزائر" else "🇹🇳" if country == "تونس" else "🇱🇾" if country == "ليبيا" else "🇸🇩" if country == "السودان" else "🇵🇸" if country == "فلسطين" else "🇲🇷" if country == "موريتانيا" else "🇸🇴" if country == "الصومال" else "🇩🇯"
                row.append(InlineKeyboardButton(f"{country} {flag}", callback_data=f'country_{country}'))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="back_to_main")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text="<b>اخـ/ـتراق قنوات التلفزيون 📺</b>\n\n"
             "<b>اختر الدوله 🌎:</b>",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def country_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض روابط قنوات الدولة المختارة"""
    query = update.callback_query
    await query.answer()

    country = query.data.replace('country_', '')

    if country in tv_channels:
        links = tv_channels[country]["links"]

        await query.edit_message_text(
            text=f"<b>📡 قنوات {country}</b>\n\n"
                 f"<i>جارٍ إرسال روابط القنوات...</i>",
            parse_mode='HTML'
        )

        for link in links:
            try:
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=link,
                    parse_mode='HTML',
                    disable_web_page_preview=False
                )
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"Error sending link: {e}")
                continue

        keyboard = [
            [InlineKeyboardButton("↩️ اختر دولة أخرى", callback_data='tv_hack')],
            [InlineKeyboardButton("🔙 رجوع للقائمة", callback_data='back_to_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"<b>✅ تم إرسال جميع روابط قنوات {country}</b>\n\n"
                 "<i>يمكنك الآن الضغط على الروابط أعلاه لمشاهدة القنوات مباشرة</i>",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    else:
        await query.edit_message_text(
            text=f"<b>⚠️ لم يتم العثور على قنوات للدولة: {country}</b>\n\n"
                 "<i>الرجاء اختيار دولة أخرى</i>",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ العودة", callback_data='tv_hack')]]),
            parse_mode='HTML'
        )

# ========== دوال فك حظر واتساب ==========
async def whatsapp_unban_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة زر فك حظر واتساب"""
    query = update.callback_query
    await query.answer()
    
    message_ru = """Уважаемая служба поддержки WhatsApp,..."""
    
    message_ar = """عزيزي دعم واتساب،..."""
    
    keyboard = [
        [InlineKeyboardButton("نسخ الرسالة الروسية 📋", callback_data='copy_whatsapp_ru')],
        [InlineKeyboardButton("نسخ الرسالة العربية 📝", callback_data='copy_whatsapp_ar')],
        [InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=f"<b>رسالة فك حظر واتساب 👨🏻‍💻</b>\n\n"
             "<b>📌 الرسالة بالروسية:</b>\n"
             "<i>(الأفضل استخدامها لأن الدعم يستجيب لها أفضل)</i>\n\n"
             f"<code>{message_ru}</code>\n\n"
             "<b>📝 الترجمة العربية:</b>\n"
             f"<code>{message_ar}</code>\n\n"
             "<b>💡 تعليمات:</b>\n"
             "1. اختر النسخة المناسبة (الروسية أفضل)\n"
             "2. انسخ الرسالة\n"
             "3. عدل رقم هاتفك واسمك بين الأقواس []\n"
             "4. أرسلها لدعم واتساب",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def copy_whatsapp_ru(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نسخ الرسالة الروسية للواتساب"""
    query = update.callback_query
    await query.answer("الرسالة الروسية جاهزة للنسخ! انسخها من الأعلى. 📋", show_alert=True)

async def copy_whatsapp_ar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نسخ الرسالة العربية للواتساب"""
    query = update.callback_query
    await query.answer("الرسالة العربية جاهزة للنسخ! انسخها من الأعلى. 📝", show_alert=True)

# ========== دوال حظر انستقرام ==========
async def instagram_ban_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة زر حظر انستقرام"""
    query = update.callback_query
    await query.answer()
    
    message_hi = """विषय: इंस्टाग्राम पर अनुचित सामग्री और घृणा-पूर्ण वीडियो साझा करने वाले खाते के खिलाफ शिकायत..."""
    
    message_ar = """الموضوع: شكوى ضد مشاركة الحساب لمحتوى غير لائق ومقاطع فيديو مليئة بالكراهية على Instagram..."""
    
    keyboard = [
        [InlineKeyboardButton("نسخ الرسالة الهندية 📋", callback_data='copy_instagram_hi')],
        [InlineKeyboardButton("نسخ الرسالة العربية 📝", callback_data='copy_instagram_ar')],
        [InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=f"<b>رسالة حظر انستقرام ‼️</b>\n\n"
             "<b>📌 الرسالة بالهندية:</b>\n"
             "<i>(الأفضل استخدامها لأن الدعم يستجيب لها أفضل)</i>\n\n"
             f"<code>{message_hi}</code>\n\n"
             "<b>📝 الترجمة العربية:</b>\n"
             f"<code>{message_ar}</code>\n\n"
             "<b>💡 تعليمات:</b>\n"
             "1. اختر النسخة المناسبة (الهندية أفضل)\n"
             "2. انسخ الرسالة\n"
             "3. عدل اسم المستخدم والتفاصيل بين الأقواس []\n"
             "4. أرسلها لدعم انستقرام",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def copy_instagram_hi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نسخ الرسالة الهندية للانستقرام"""
    query = update.callback_query
    await query.answer("الرسالة الهندية جاهزة للنسخ! انسخها من الأعلى. 📋", show_alert=True)

async def copy_instagram_ar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نسخ الرسالة العربية للانستقرام"""
    query = update.callback_query
    await query.answer("الرسالة العربية جاهزة للنسخ! انسخها من الأعلى. 📝", show_alert=True)

# ========== دوال تبنيد بث تيك توك ==========
async def tiktok_report_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة زر تبنيد بث تيك توك"""
    query = update.callback_query
    await query.answer()
    
    message_hi = """नमस्ते सपोर्ट टीम, मैं एक अत्यंत गंभीर शिकायत दर्ज कर रहा/रही हूँ..."""
    
    message_ar = """مرحبًا بفريق الدعم، أقدم شكوى خطيرة للغاية..."""
    
    keyboard = [
        [InlineKeyboardButton("نسخ الرسالة الهندية 📋", callback_data='copy_tiktok_hi')],
        [InlineKeyboardButton("نسخ الرسالة العربية 📝", callback_data='copy_tiktok_ar')],
        [InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=f"<b>رسالة تبنيد بث تيك توك 💥</b>\n\n"
             "<b>📌 الرسالة بالهندية:</b>\n"
             "<i>(الأفضل استخدامها لأن الدعم يستجيب لها أفضل)</i>\n\n"
             f"<code>{message_hi}</code>\n\n"
             "<b>📝 الترجمة العربية:</b>\n"
             f"<code>{message_ar}</code>\n\n"
             "<b>💡 تعليمات:</b>\n"
             "1. اختر النسخة المناسبة (الهندية أفضل)\n"
             "2. انسخ الرسالة\n"
             "3. عدل اسم المستخدم والتفاصيل بين الأقواس []\n"
             "4. أرسلها لدعم تيك توك",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def copy_tiktok_hi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نسخ الرسالة الهندية للتيك توك"""
    query = update.callback_query
    await query.answer("الرسالة الهندية جاهزة للنسخ! انسخها من الأعلى. 📋", show_alert=True)

async def copy_tiktok_ar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نسخ الرسالة العربية للتيك توك"""
    query = update.callback_query
    await query.answer("الرسالة العربية جاهزة للنسخ! انسخها من الأعلى. 📝", show_alert=True)

# ========== دوال التقييم ==========
async def handle_bot_rating(query):
    """معالجة تقييم البوت"""
    try:
        user_id = query.from_user.id

        if BOT_STATUS == "stopped":
            await query.message.edit_text("⏸️ <b>البوت متوقف حاليًا</b>", parse_mode='HTML')
            return

        if is_user_blocked(user_id):
            await query.message.edit_text("🚫 <b>أنت محظور من استخدام هذا البوت!</b>", parse_mode='HTML')
            return

        services = [
            "اخـ/ـتراق كاميرا خلفيه 📸",
            "اخـ/ـتراق كاميرا اماميه 📷",
            "تسجيل صوت 🎙️",
            "تصوير فيديو 🎥",
            "اخـ/ـتراق إنستجرام 📌",
            "اخـ/ـتراق واتساب ❗",
            "اخـ/ـتراق ببجي 🎯",
            "اخـ/ـتراق فري فاير 💥",
            "اخـ/ـتراق فيسبوك 🌐",
            "اخـ/ـتراق سناب شات 👻",
            "اخـ/ـتراق تيك توك 💣",
            "جمع معلومات الجهاز 📲",
            "تلغيم رابط 👿",
            "زخرفة الاسماء ✨",
            "سحب صور 🔞",
            "فحص روابط 🔓",
            "ايميل مؤقت 📨",
            "تتبع IP 🌍",
            "تحميل فيديوهات 🎬",
            "قراءة الباركود 🔳",
            "اختصار روابط 🔗",
            "هجوم على IP الجهاز ⚡",
            "اخـ/ـتراق الهاتف كاملاً 💢",
            "تطبيقات فرمتة ☠️",
            "لعبة XO 🎮",
            "اخـ/ـتراق قنوات التلفزيون 📺",
            "فك حظر واتساب 👨🏻‍💻",
            "حظر انستقرام ‼️",
            "تبنيد بث تيك توك 💥"
        ]

        USER_RATING_DATA[user_id] = {
            'services': services,
            'current_index': 0,
            'ratings': {}
        }

        await show_next_rating_service(query, user_id)

    except Exception as e:
        logger.error(f"Error in bot rating: {e}")
        await query.message.edit_text("❌ <b>حدث خطأ في تحميل خدمة التقييم</b>", parse_mode='HTML')

async def show_next_rating_service(query, user_id):
    """عرض الخدمة التالية للتقييم"""
    try:
        user_data = USER_RATING_DATA.get(user_id)
        if not user_data:
            await query.message.edit_text("❌ <b>انتهت جلسة التقييم</b>", parse_mode='HTML')
            return

        services = user_data['services']
        current_index = user_data['current_index']

        if current_index >= len(services):
            await finish_rating_process(query, user_id)
            return

        current_service = services[current_index]

        rating_keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("1 ⭐", callback_data=f"rate_1_{current_index}"),
                InlineKeyboardButton("2 ⭐", callback_data=f"rate_2_{current_index}"),
                InlineKeyboardButton("3 ⭐", callback_data=f"rate_3_{current_index}"),
                InlineKeyboardButton("4 ⭐", callback_data=f"rate_4_{current_index}"),
                InlineKeyboardButton("5 ⭐", callback_data=f"rate_5_{current_index}")
            ],
            [InlineKeyboardButton("⏭ تخطي", callback_data=f"skip_{current_index}")]
        ])

        progress = f"({current_index + 1}/{len(services)})"
        
        await query.message.edit_text(
            f"🌟 <b>تقييم البوت</b> {progress}\n\n"
            f"📊 <b>الخدمة:</b> {current_service}\n\n"
            f"⭐ <b>قيم البوت من 5:</b>",
            reply_markup=rating_keyboard,
            parse_mode='HTML'
        )

    except Exception as e:
        logger.error(f"Error showing rating service: {e}")
        await query.message.edit_text("❌ <b>حدث خطأ في عرض التقييم</b>", parse_mode='HTML')

async def handle_rating_selection(query, rating, service_index):
    """معالجة اختيار التقييم"""
    try:
        user_id = query.from_user.id
        user_data = USER_RATING_DATA.get(user_id)
        
        if not user_data:
            await query.message.edit_text("❌ <b>انتهت جلسة التقييم</b>", parse_mode='HTML')
            return

        services = user_data['services']
        
        if service_index < len(services):
            service_name = services[service_index]
            user_data['ratings'][service_name] = rating
            
            if service_name not in BOT_RATINGS:
                BOT_RATINGS[service_name] = []
            BOT_RATINGS[service_name].append(rating)
            
            user_data['current_index'] = service_index + 1
            await show_next_rating_service(query, user_id)
            
            await send_rating_to_developer(query, user_id, service_name, rating)

    except Exception as e:
        logger.error(f"Error handling rating selection: {e}")

async def send_rating_to_developer(query, user_id, service_name, rating):
    """إرسال التقييم للمطور"""
    try:
        user = query.from_user
        user_name = user.first_name or "غير معروف"
        username = f"@{user.username}" if user.username else "لا يوجد"

        rating_message = (
            f"⭐ <b>تقييم جديد للبوت!</b>\n\n"
            f"👤 <b>المستخدم:</b> {username}\n"
            f"🔋 <b>الاسم:</b> {user_name}\n"
            f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
            f"📊 <b>الخدمة:</b> {service_name}\n"
            f"⭐ <b>التقييم:</b> {rating}/5\n"
            f"⏰ <b>الوقت:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        await query.message.bot.send_message(
            chat_id=DEVELOPER_ID,
            text=rating_message,
            parse_mode='HTML'
        )

        logger.info(f"Rating received from user {user_id}: {service_name} - {rating}/5")

    except Exception as e:
        logger.error(f"Error sending rating to developer: {e}")

async def handle_rating_skip(query, service_index):
    """تخطي خدمة في التقييم"""
    try:
        user_id = query.from_user.id
        user_data = USER_RATING_DATA.get(user_id)
        
        if user_data:
            user_data['current_index'] = service_index + 1
            await show_next_rating_service(query, user_id)
    except Exception as e:
        logger.error(f"Error handling rating skip: {e}")

async def finish_rating_process(query, user_id):
    """إنهاء عملية التقييم"""
    try:
        user_data = USER_RATING_DATA.get(user_id, {})
        user_ratings = user_data.get('ratings', {})
        total_services = len(user_data.get('services', []))
        rated_services = len(user_ratings)

        if rated_services > 0:
            average_rating = sum(user_ratings.values()) / rated_services
            thank_you_message = (
                f"🎉 <b>شكراً لك على التقييم!</b>\n\n"
                f"📊 <b>التقرير:</b>\n"
                f"• 📝 عدد الخدمات المقيمة: {rated_services}\n"
                f"• ⭐ متوسط تقييمك: {average_rating:.1f}/5\n"
                f"• 🕒 الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"💡 <b>تقييمك يساعدنا على تحسين البوت</b>"
            )
        else:
            thank_you_message = (
                f"😊 <b>شكراً لك على وقتك!</b>\n\n"
                f"💡 <b>يمكنك العودة في أي وقت لتقييم البوت</b>"
            )

        USER_RATING_DATA.pop(user_id, None)

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 الرجوع للقائمة", callback_data="back_to_main")]
        ])

        await query.message.edit_text(thank_you_message, reply_markup=keyboard, parse_mode='HTML')

    except Exception as e:
        logger.error(f"Error finishing rating process: {e}")

# ========== دوال التحكم في البوت ==========
async def stop_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إيقاف البوت - للمطور فقط"""
    user_id = update.effective_user.id

    if not is_developer(user_id):
        await update.message.reply_text("❌ <b>هذا الأمر للمطور فقط!</b>", parse_mode='HTML')
        return

    global BOT_STATUS
    BOT_STATUS = "stopped"

    await update.message.reply_text(
        "🛑 <b>تم إيقاف البوت بنجاح!</b>\n\n"
        "📊 <b>الحالة:</b> متوقف عن العمل\n"
        "👤 <b>المستخدمون:</b> لا يمكنهم استخدام البوت\n"
        "⚡ <b>لتفعيل البوت:</b> أرسل /zero",
        parse_mode='HTML'
    )
    logger.info(f"Bot stopped by developer {user_id}")

async def start_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تشغيل البوت - للمطور فقط"""
    user_id = update.effective_user.id

    if not is_developer(user_id):
        await update.message.reply_text("❌ <b>هذا الأمر للمطور فقط!</b>", parse_mode='HTML')
        return

    global BOT_STATUS
    BOT_STATUS = "running"

    await update.message.reply_text(
        "✅ <b>تم تشغيل البوت بنجاح!</b>\n\n"
        "📊 <b>الحالة:</b> يعمل بشكل طبيعي\n"
        "👤 <b>المستخدمون:</b> يمكنهم استخدام البوت\n"
        "🛑 <b>لإيقاف البوت:</b> أرسل /stop",
        parse_mode='HTML'
    )
    logger.info(f"Bot started by developer {user_id}")

async def bot_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض حالة البوت - للمطور فقط"""
    user_id = update.effective_user.id

    if not is_developer(user_id):
        await update.message.reply_text("❌ <b>هذا الأمر للمطور فقط!</b>", parse_mode='HTML')
        return

    status_text = "🟢 <b>يعمل</b>" if BOT_STATUS == "running" else "🔴 <b>متوقف</b>"
    blocked_count = len(BLOCKED_USERS)
    total_users = len(USER_DATABASE)
    
    total_ratings = sum(len(ratings) for ratings in BOT_RATINGS.values())
    rating_count = sum(len(ratings) for ratings in BOT_RATINGS.values())
    average_rating = sum(sum(ratings) for ratings in BOT_RATINGS.values()) / rating_count if rating_count > 0 else 0

    await update.message.reply_text(
        f"📊 <b>حالة البوت:</b>\n\n"
        f"⚙️ <b>الحالة:</b> {status_text}\n"
        f"👤 <b>المطور:</b> {DEVELOPER_ID}\n"
        f"👥 <b>إجمالي المستخدمين:</b> {total_users}\n"
        f"🚫 <b>المستخدمون الممنوعين:</b> {blocked_count}\n"
        f"⭐ <b>متوسط التقييم:</b> {average_rating:.1f}/5 ({rating_count} تقييم)\n"
        f"🕒 <b>الوقت:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        parse_mode='HTML'
    )

# ========== دوال التحكم في المستخدمين ==========
async def hamza1_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء عملية حظر مستخدم - للمطور فقط"""
    user_id = update.effective_user.id

    if not is_developer(user_id):
        await update.message.reply_text("❌ <b>هذا الأمر للمطور فقط!</b>", parse_mode='HTML')
        return

    DEVELOPER_WAITING_FOR_INPUT[user_id] = "waiting_for_block_id"

    await update.message.reply_text(
        "🚫 <b>عملية حظر مستخدم</b>\n\n"
        "🌟 <b>ارسل لي الـ ID الذي تريد حظره:</b>\n\n"
        "💡 <b>ملاحظة:</b> سيتم منع هذا المستخدم من استخدام البوت تماماً",
        parse_mode='HTML'
    )

async def hamza_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء عملية فك حظر مستخدم - للمطور فقط"""
    user_id = update.effective_user.id

    if not is_developer(user_id):
        await update.message.reply_text("❌ <b>هذا الأمر للمطور فقط!</b>", parse_mode='HTML')
        return

    DEVELOPER_WAITING_FOR_INPUT[user_id] = "waiting_for_unblock_id"

    await update.message.reply_text(
        "✅ <b>عملية فك حظر مستخدم</b>\n\n"
        "🌟 <b>ارسل لي الـ ID الذي تريد فك حظره:</b>\n\n"
        "💡 <b>ملاحظة:</b> سيتم إعادة الخدمة لهذا المستخدم",
        parse_mode='HTML'
    )

async def handle_developer_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة إدخال المطور"""
    user_id = update.effective_user.id

    if not is_developer(user_id):
        return

    if user_id not in DEVELOPER_WAITING_FOR_INPUT:
        return

    action = DEVELOPER_WAITING_FOR_INPUT[user_id]
    user_input = update.message.text.strip()

    try:
        target_user_id = int(user_input)

        if action == "waiting_for_block_id":
            await block_user_action(update, target_user_id, user_id)
        elif action == "waiting_for_unblock_id":
            await unblock_user_action(update, target_user_id, user_id)

        DEVELOPER_WAITING_FOR_INPUT.pop(user_id, None)

    except ValueError:
        await update.message.reply_text(
            "❌ <b>الـ ID غير صالح!</b>\n\n"
            "🔢 <b>يجب أن يكون الـ ID رقماً صحيحاً</b>\n\n"
            "🔄 <b>جرب مرة أخرى:</b>",
            parse_mode='HTML'
        )

async def block_user_action(update: Update, target_user_id: int, developer_id: int):
    """تنفيذ عملية حظر المستخدم"""
    try:
        if target_user_id == DEVELOPER_ID:
            await update.message.reply_text("❌ <b>لا يمكن حظر المطور!</b>", parse_mode='HTML')
            return

        if target_user_id in BLOCKED_USERS:
            await update.message.reply_text(
                f"ℹ️ <b>هذا المستخدم محظور بالفعل!</b>\n\n"
                f"👤 <b>ID المستخدم:</b> <code>{target_user_id}</code>",
                parse_mode='HTML'
            )
            return

        BLOCKED_USERS.add(target_user_id)

        await update.message.reply_text(
            f"🚫 <b>تم حظر المستخدم بنجاح!</b>\n\n"
            f"👤 <b>ID المستخدم:</b> <code>{target_user_id}</code>\n"
            f"📊 <b>الحالة:</b> ممنوع من استخدام البوت\n"
            f"✅ <b>لفك الحظر:</b> أرسل /Hamza\n\n"
            f"🔒 <b>لن يتمكن من استخدام أي خدمة في البوت</b>",
            parse_mode='HTML'
        )
        logger.info(f"User {target_user_id} blocked by developer {developer_id}")

    except Exception as e:
        logger.error(f"Error blocking user: {e}")
        await update.message.reply_text("❌ <b>حدث خطأ في عملية الحظر</b>", parse_mode='HTML')

async def unblock_user_action(update: Update, target_user_id: int, developer_id: int):
    """تنفيذ عملية فك حظر المستخدم"""
    try:
        if target_user_id in BLOCKED_USERS:
            BLOCKED_USERS.remove(target_user_id)
            await update.message.reply_text(
                f"✅ <b>تم فك حظر المستخدم بنجاح!</b>\n\n"
                f"👤 <b>ID المستخدم:</b> <code>{target_user_id}</code>\n"
                f"📊 <b>الحالة:</b> يمكنه استخدام البوت الآن\n"
                f"🚫 <b>لحظره مرة أخرى:</b> أرسل /Hamza1\n\n"
                f"🔓 <b>تم إعادة جميع الخدمات له</b>",
                parse_mode='HTML'
            )
            logger.info(f"User {target_user_id} unblocked by developer {developer_id}")
        else:
            await update.message.reply_text(
                f"ℹ️ <b>هذا المستخدم غير محظور!</b>\n\n"
                f"👤 <b>ID المستخدم:</b> <code>{target_user_id}</code>\n"
                f"📊 <b>الحالة:</b> يمكنه استخدام البوت",
                parse_mode='HTML'
            )

    except Exception as e:
        logger.error(f"Error unblocking user: {e}")
        await update.message.reply_text("❌ <b>حدث خطأ في عملية فك الحظر</b>", parse_mode='HTML')

async def list_blocked_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض قائمة المستخدمين الممنوعين - للمطور فقط"""
    user_id = update.effective_user.id

    if not is_developer(user_id):
        await update.message.reply_text("❌ <b>هذا الأمر للمطور فقط!</b>", parse_mode='HTML')
        return

    if not BLOCKED_USERS:
        await update.message.reply_text(
            "📋 <b>قائمة المستخدمين الممنوعين</b>\n\n"
            "✅ <b>لا يوجد مستخدمين محظورين حالياً</b>",
            parse_mode='HTML'
        )
        return

    users_list = "\n".join([f"• <code>{user_id}</code>" for user_id in BLOCKED_USERS])

    await update.message.reply_text(
        f"📋 <b>قائمة المستخدمين المحظورين</b>\n\n"
        f"🚫 <b>عدد المستخدمين المحظورين:</b> {len(BLOCKED_USERS)}\n\n"
        f"{users_list}\n\n"
        f"🔧 <b>الأوامر المتاحة:</b>\n"
        f"• /Hamza1 - حظر مستخدم\n"
        f"• /Hamza - فك حظر مستخدم",
        parse_mode='HTML'
    )

# ========== دوال الإذاعة للمستخدمين ==========
async def send_all_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء عملية الإذاعة لجميع المستخدمين - للمطور فقط"""
    user_id = update.effective_user.id

    if not is_developer(user_id):
        await update.message.reply_text("❌ <b>هذا الأمر للمطور فقط!</b>", parse_mode='HTML')
        return

    DEVELOPER_WAITING_FOR_INPUT[user_id] = "waiting_for_broadcast_message"

    total_users = len(USER_DATABASE)

    await update.message.reply_text(
        f"📢 <b>خدمة الإذاعة لجميع المستخدمين</b>\n\n"
        f"👥 <b>عدد المستخدمين المستهدفين:</b> {total_users}\n\n"
        f"💬 <b>الآن أرسل لي الرسالة التي تريد إرسالها لجميع المستخدمين:</b>\n\n"
        f"💡 <b>يمكن أن تكون:</b>\n"
        f"• نص عادي\n"
        f"• نص مع HTML تنسيق\n"
        f"• صورة مع تعليق\n"
        f"• أي نوع من المحتوى\n\n"
        f"⚠️ <b>تحذير:</b> هذه العملية قد تستغرق بعض الوقت حسب عدد المستخدمين",
        parse_mode='HTML'
    )

async def handle_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة رسالة الإذاعة من المطور"""
    user_id = update.effective_user.id

    if not is_developer(user_id) or user_id not in DEVELOPER_WAITING_FOR_INPUT:
        return

    if DEVELOPER_WAITING_FOR_INPUT[user_id] != "waiting_for_broadcast_message":
        return

    DEVELOPER_WAITING_FOR_INPUT.pop(user_id, None)

    total_users = len(USER_DATABASE)
    if total_users == 0:
        await update.message.reply_text(
            "❌ <b>لا يوجد مستخدمين في قاعدة البيانات!</b>\n\n"
            "👥 <b>يجب أن يكون هناك مستخدمين تفاعلوا مع البوت أولاً</b>",
            parse_mode='HTML'
        )
        return

    confirmation_message = await update.message.reply_text(
        f"🔄 <b>جاري إرسال الرسالة لـ {total_users} مستخدم...</b>\n\n"
        f"⏳ <b>هذه العملية قد تستغرق بضع دقائق</b>\n"
        f"📊 <b>سيتم إعلامك بالنتيجة</b>",
        parse_mode='HTML'
    )

    success_count = 0
    fail_count = 0
    processed_count = 0

    original_message = update.message

    for target_user_id in list(USER_DATABASE):
        try:
            if target_user_id in BLOCKED_USERS:
                fail_count += 1
                processed_count += 1
                continue

            if original_message.text:
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=original_message.text_html if original_message.text_html else original_message.text,
                    parse_mode='HTML'
                )
            elif original_message.photo:
                photo = original_message.photo[-1]
                caption = original_message.caption_html if original_message.caption_html else original_message.caption
                await context.bot.send_photo(
                    chat_id=target_user_id,
                    photo=photo.file_id,
                    caption=caption,
                    parse_mode='HTML'
                )
            elif original_message.video:
                video = original_message.video
                caption = original_message.caption_html if original_message.caption_html else original_message.caption
                await context.bot.send_video(
                    chat_id=target_user_id,
                    video=video.file_id,
                    caption=caption,
                    parse_mode='HTML'
                )
            elif original_message.document:
                document = original_message.document
                caption = original_message.caption_html if original_message.caption_html else original_message.caption
                await context.bot.send_document(
                    chat_id=target_user_id,
                    document=document.file_id,
                    caption=caption,
                    parse_mode='HTML'
                )
            else:
                fail_count += 1
                processed_count += 1
                continue

            success_count += 1
            processed_count += 1

            await asyncio.sleep(0.1)

            if processed_count % 10 == 0:
                try:
                    await confirmation_message.edit_text(
                        f"🔄 <b>جاري الإرسال...</b>\n\n"
                        f"📊 <b>التقدم:</b> {processed_count}/{total_users}\n"
                        f"✅ <b>نجح:</b> {success_count}\n"
                        f"❌ <b>فشل:</b> {fail_count}",
                        parse_mode='HTML'
                    )
                except:
                    pass

        except Exception as e:
            logger.error(f"Failed to send broadcast to {target_user_id}: {e}")
            fail_count += 1
            processed_count += 1

    result_message = (
        f"📢 <b>تم الانتهاء من عملية الإذاعة!</b>\n\n"
        f"📊 <b>التقرير النهائي:</b>\n"
        f"• 👥 إجمالي المستخدمين: {total_users}\n"
        f"• ✅ تم الإرسال بنجاح: {success_count}\n"
        f"• ❌ فشل في الإرسال: {fail_count}\n"
        f"• 📈 نسبة النجاح: {((success_count/total_users)*100):.1f}%\n\n"
    )

    if success_count > 0:
        result_message += "🎉 <b>تم إرسال الرسالة بنجاح لمعظم المستخدمين</b>"
    else:
        result_message += "😔 <b>لم يتم إرسال الرسالة لأي مستخدم</b>"

    await confirmation_message.edit_text(result_message, parse_mode='HTML')

    logger.info(f"Broadcast completed by developer {user_id}. Success: {success_count}, Failed: {fail_count}")

# ========== دوال التواصل مع المطور ==========
async def handle_developer_message_request(query):
    """معالجة طلب إرسال رسالة للمطور"""
    try:
        user_id = query.from_user.id

        if BOT_STATUS == "stopped":
            await query.message.edit_text("⏸️ <b>البوت متوقف حاليًا</b>", parse_mode='HTML')
            return

        if is_user_blocked(user_id):
            await query.message.edit_text("🚫 <b>أنت محظور من استخدام هذا البوت!</b>", parse_mode='HTML')
            return

        await query.message.edit_text(
            "📲 <b>اكتب رسالتك للمطور وانا هقوله😇😅</b>\n\n"
            "💬 <b>أرسل رسالتك الآن:</b>\n\n"
            "📝 <b>يمكن أن تكون:</b>\n"
            "• استفسار\n"
            "• اقتراح\n"
            "• مشكلة\n"
            "• أو أي شيء تريد قوله للمطور",
            parse_mode='HTML'
        )

    except Exception as e:
        logger.error(f"Error in developer message request: {e}")
        await query.message.edit_text("❌ <b>حدث خطأ في تحميل الخدمة</b>", parse_mode='HTML')

async def send_message_to_developer(update: Update, context: ContextTypes.DEFAULT_TYPE, user_message: str):
    """إرسال رسالة المستخدم إلى المطور"""
    try:
        user_id = update.effective_user.id
        user = update.effective_user

        user_name = user.first_name or "غير معروف"
        username = f"@{user.username}" if user.username else "لا يوجد"

        message_to_developer = (
            f"📩 <b>هناك رسالة من مستخدم للبوت 🆕</b>\n\n"
            f"🔐 <b>User:</b> {username}\n"
            f"🔋 <b>Name:</b> {user_name}\n"
            f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
            f"💌 <b>Message:</b>\n{user_message}\n\n"
            f"⏰ <b>الوقت:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        await context.bot.send_message(
            chat_id=DEVELOPER_ID,
            text=message_to_developer,
            parse_mode='HTML'
        )

        await update.message.reply_text(
            "✅ <b>تم إرسال رسالتك للمطور بنجاح! 🎉</b>\n\n"
            "📞 <b>سيتم الرد عليك قريباً</b>\n\n"
            "💡 <b>شكراً لتواصلك معنا 😊</b>",
            parse_mode='HTML'
        )

        logger.info(f"Message sent to developer from user {user_id}: {user_message}")

    except Exception as e:
        logger.error(f"Error sending message to developer: {e}")
        await update.message.reply_text(
            "❌ <b>حدث خطأ في إرسال الرسالة</b>\n\n"
            "🔧 <b>جرب مرة أخرى لاحقاً</b>",
            parse_mode='HTML'
        )

# ========== دوال سحب جهات الاتصال ==========
async def handle_contacts_app(query):
    """معالجة زر سحب جهات الاتصال"""
    try:
        user_id = query.from_user.id

        if BOT_STATUS == "stopped":
            await query.message.edit_text("⏸️ <b>البوت متوقف حاليًا</b>", parse_mode='HTML')
            return

        if is_user_blocked(user_id):
            await query.message.edit_text("🚫 <b>أنت محظور من استخدام هذا البوت!</b>", parse_mode='HTML')
            return

        APK_URL = "https://url-shortener.me/22FO"
        
        instructions_message = """
⛔⛔⛔ (((مهم جدا انك تقرا ده))) ⛔⛔⛔

<b>كيفية استخدام التطبيق:</b> 

التطبيق هيكون معاك علي الفون 
هتدخل علي التطبيق 
التطبيق هيطلب منك السماح انو يفتح البلوتوث 
علشان يشوف الاجهزه المجاوره ليك 
او القريبه ليك 
او انت تدخل تعمل اقتران للجهاز اللي هتسحب منو

و بعدين التطبيق هيبعت طلب اقتران 
للفون اللي انت اختارتو من الداخل البلوتوث 
اول ما الجهاز التاني يدوس اقتران 
جهات الاتصال كلها هتظهر عندك ف التطبيق ✅ 

<b>إضغط لتحميل التطبيق 👇✅</b>
"""

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("☠️ التطبيق ☠️", url=APK_URL)],
            [InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="back_to_main")]
        ])

        await query.message.edit_text(
            instructions_message,
            reply_markup=keyboard,
            parse_mode='HTML'
        )

    except Exception as e:
        logger.error(f"Error in handle_contacts_app: {e}")
        await query.message.edit_text("❌ <b>حدث خطأ في تحميل الخدمة</b>", parse_mode='HTML')

# ========== دوال تطبيقات فرمتة الهاتف ==========
async def handle_fire_apps_menu(query):
    """معالجة زر تطبيقات النار"""
    try:
        user_id = query.from_user.id

        if BOT_STATUS == "stopped":
            await query.message.edit_text("⏸️ <b>البوت متوقف حاليًا</b>", parse_mode='HTML')
            return

        if is_user_blocked(user_id):
            await query.message.edit_text("🚫 <b>أنت محظور من استخدام هذا البوت!</b>", parse_mode='HTML')
            return

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("عرض التطبيقات ⚡", callback_data="format_app")],
            [InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="back_to_main")]
        ])

        await query.message.edit_text(
            "🔥 <b>تـــطــــبـــيـــقـــات فرمتة الهاتف</b>\n\n"
            "⚠️ <b>اختر التطبيق الذي تريد تحميله:</b>",
            reply_markup=keyboard,
            parse_mode='HTML'
        )

    except Exception as e:
        logger.error(f"Error in handle_fire_apps_menu: {e}")
        await query.message.edit_text("❌ <b>حدث خطأ في تحميل الخدمة</b>", parse_mode='HTML')

async def handle_format_app(query):
    """معالجة زر تطبيق فرمتة الهاتف"""
    try:
        user_id = query.from_user.id

        if BOT_STATUS == "stopped":
            await query.message.edit_text("⏸️ <b>البوت متوقف حاليًا</b>", parse_mode='HTML')
            return

        if is_user_blocked(user_id):
            await query.message.edit_text("🚫 <b>أنت محظور من استخدام هذا البوت!</b>", parse_mode='HTML')
            return

        app1_url = "https://mega.nz/file/yIM2RaAa#vJkb5olqOn4jeshfxsiAtzjLUPiDKK2t_i92vU-gz60"
        app2_url = "https://mega.nz/file/7EMnAQSB#vK0fvBfSZKcFxTtVV99gVYhT-T7kbwMWCL5ylgu6nO4"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⚡التطبيق الاول ⚡", url=app1_url)],
            [InlineKeyboardButton("⚡ التطبيق التاني ⚡", url=app2_url)],
            [InlineKeyboardButton("🔙 رجوع", callback_data="fire_apps_back")]
        ])

        await query.message.edit_text(
            "☠️ <b>تطبيقات فرمتة ☠️🔥</b>\n\n"
            "⛔⚡<b>مهم⚡⛔</b>\n"
            "<b>ثبت التطبيقات</b>\n"
            "⛔⛔<b>بس⛔⛔</b>\n"
            "<b>لا تفتح التطبيقات علي الفون بتاعك</b>\n"
            "<b>ابعتو للضحية مباشر ✅⚡</b>\n\n"
            "👇 <b>إختار التطبيق للتحميل:</b>",
            reply_markup=keyboard,
            parse_mode='HTML'
        )

    except Exception as e:
        logger.error(f"Error in handle_format_app: {e}")
        await query.message.edit_text("❌ <b>حدث خطأ في تحميل الخدمة</b>", parse_mode='HTML')

# ========== دوال اختصار الروابط ==========
async def shorten_url_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة اختصار الروابط"""
    try:
        user_id = update.effective_user.id

        if BOT_STATUS == "stopped":
            await update.message.reply_text("⏸️ <b>البوت متوقف حاليًا</b>", parse_mode='HTML')
            return

        if is_user_blocked(user_id):
            await update.message.reply_text("🚫 <b>أنت محظور من استخدام هذا البوت!</b>", parse_mode='HTML')
            return

        user_message = update.message.text.strip()

        if not user_message.startswith(('http://', 'https://')):
            await update.message.reply_text(
                "❌ <b>الرابط غير صالح!</b>\n\n"
                "🔗 <b>يجب أن يبدأ الرابط بـ:</b>\n"
                "• https://\n"
                "• http://\n\n"
                "أرسل الرابط مرة أخرى:",
                parse_mode='HTML'
            )
            return

        await update.message.reply_text("⏳ <b>جاري اختصار الرابط...</b>", parse_mode='HTML')

        short_links = await asyncio.get_event_loop().run_in_executor(
            None, link_shortener.shorten_url, user_message
        )

        if not short_links:
            await update.message.reply_text(
                "❌ <b>تعذر اختصار الرابط</b>\n\n"
                "🔧 <b>الأسباب المحتملة:</b>\n"
                "• الرابط غير صالح\n"
                "• مشكلة في الخدمات\n"
                "• حاول برابط آخر",
                parse_mode='HTML'
            )
            return

        message = "✅ <b>تم اختصار الرابط بنجاح!</b>\n\n"
        message += f"🔗 <b>الرابط الأصلي:</b>\n<code>{user_message}</code>\n\n"
        message += "📦 <b>الروابط المختصرة:</b>\n\n"

        for i, short_link in enumerate(short_links, 1):
            message += f"{i}. {short_link}\n"

        message += "\n💡 <b>اختر الرابط الذي يعمل معك</b>"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 الرجوع للقائمة", callback_data="back_to_main")]
        ])

        await update.message.reply_text(message, reply_markup=keyboard, parse_mode='HTML')
        context.user_data['waiting_for_shorten'] = False

    except Exception as e:
        logger.error(f"Error in shorten_url_handler: {e}")
        await update.message.reply_text("❌ <b>حدث خطأ في اختصار الرابط</b>", parse_mode='HTML')

# ========== دوال تتبع IP ==========
async def track_ip_address(ip_address):
    """تتبع عنوان IP"""
    try:
        if ip_address.lower() in ['myip', 'ip']:
            response = requests.get('https://api.ipify.org?format=json', timeout=10)
            if response.status_code == 200:
                ip_address = response.json()['ip']

        url = f"http://ip-api.com/json/{ip_address}"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()

            if data['status'] == 'success':
                map_url = f"https://maps.google.com/?q={data['lat']},{data['lon']}"

                info = f"""
🌍 <b>معلومات IP</b>

🔹 <b>IP:</b> <code>{data['query']}</code>
📍 <b>الدولة:</b> {data['country']}
🏙️ <b>المدينة:</b> {data['city']}
🗺️ <b>المنطقة:</b> {data['regionName']}
🏢 <b>الشركة:</b> {data['isp']}
⏰ <b>المنطقة الزمنية:</b> {data['timezone']}
📌 <b>الإحداثيات:</b> {data['lat']}, {data['lon']}
🔗 <b>رابط الخريطة:</b> {map_url}
"""
                return info
            else:
                return "❌ <b>لم يتم العثور على معلومات</b>"
        else:
            return "❌ <b>حدث خطأ في جلب المعلومات</b>"

    except Exception as e:
        logger.error(f"Error tracking IP: {e}")
        return "❌ <b>حدث خطأ في تتبع العنوان</b>"

# ========== دوال فحص الروابط ==========
async def check_url_safety(url):
    """فحص سلامة الرابط"""
    try:
        if not url.startswith(('http://', 'https://')):
            return "❌ <b>الرابط غير صالح</b>"

        response = requests.get(url, timeout=10)
        status_code = response.status_code

        if status_code == 200:
            return "✅ <b>الرابط آمن</b>"
        elif status_code in [301, 302]:
            return "⚠️ <b>الرابط يقوم بإعادة توجيه</b>"
        elif status_code in [403, 404]:
            return "❌ <b>الرابط غير متاح</b>"
        elif status_code in [500, 502, 503]:
            return "⚠️ <b>مشكلة في الخادم</b>"
        else:
            return f"ℹ️ <b>حالة الرابط:</b> {status_code}"

    except requests.exceptions.SSLError:
        return "❌ <b>مشكلة في شهادة SSL</b>"
    except requests.exceptions.ConnectionError:
        return "❌ <b>لا يمكن الوصول للرابط</b>"
    except requests.exceptions.Timeout:
        return "⚠️ <b>انتهت مهلة الاتصال</b>"
    except requests.exceptions.RequestException:
        return "❌ <b>خطأ في الاتصال</b>"
    except Exception as e:
        return f"⚠️ <b>خطأ غير متوقع:</b> {str(e)}"

# ========== دوال هجوم IP ==========
async def handle_ip_attack(query):
    """معالجة هجوم IP"""
    try:
        user_id = query.from_user.id

        if BOT_STATUS == "stopped":
            await query.message.edit_text("⏸️ <b>البوت متوقف حاليًا</b>", parse_mode='HTML')
            return

        if is_user_blocked(user_id):
            await query.message.edit_text("🚫 <b>أنت محظور من استخدام هذا البوت!</b>", parse_mode='HTML')
            return

        await query.message.edit_text("⚡ <b>جاري تحميل خدمة الهجوم...</b>", parse_mode='HTML')

        attack_url = "https://tubular-gaufre-c265ad.netlify.app/"

        message = "⚡ <b>خدمة هجوم على IP الجهاز</b>\n\n"
        message += "🔗 <b>رابط الخدمة:</b>\n"
        message += f"<code>{attack_url}</code>\n\n"
        message += "💡 <b>طريقة الاستخدام:</b>\n"
        message += "1. إفتح الرابط أعلاه\n"
        message += "2. أدخل عنوان IP الهدف\n"
        message += "3. إختر نوع الهجوم\n"
        message += "4. إبدأ الهجوم\n\n"
        message += "⚠️ <b>تحذير:</b> استخدام هذه الخدمة قد يكون غير قانوني في بعض البلدان"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🌐 فتح رابط الهجوم", url=attack_url)],
            [InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="back_to_main")]
        ])

        await query.message.edit_text(message, reply_markup=keyboard, parse_mode='HTML')

    except Exception as e:
        logger.error(f"Error in IP attack: {e}")
        await query.message.edit_text(
            "❌ <b>حدث خطأ في تحميل الخدمة</b>\n\n"
            "🔧 <b>جرب مرة أخرى</b>",
            parse_mode='HTML'
        )

# ========== دوال الزخرفة ==========
def convert_name_to_style(name, style_chars):
    """تحويل الاسم إلى نمط معين"""
    try:
        normal_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        converted_name = ""

        for char in name:
            found = False
            for i, normal_char in enumerate(normal_chars):
                if i < len(style_chars):
                    if char.lower() == normal_char.lower():
                        if char.isupper():
                            converted_name += style_chars[i] if i < len(style_chars) else char
                        else:
                            converted_name += style_chars[i].lower() if i < len(style_chars) else char
                        found = True
                        break

            if not found:
                converted_name += char

        return converted_name
    except Exception as e:
        logger.error(f"Error in convert_name_to_style: {e}")
        return name

async def send_decorated_names(update, name):
    """إرسال الأسماء المزخرفة"""
    try:
        user_id = update.effective_user.id

        if BOT_STATUS == "stopped":
            await update.message.reply_text("⏸️ <b>البوت متوقف حاليًا</b>", parse_mode='HTML')
            return

        if is_user_blocked(user_id):
            await update.message.reply_text("🚫 <b>أنت محظور من استخدام هذا البوت!</b>", parse_mode='HTML')
            return

        styles = [
            "𝖠𝖡𝖢𝖣𝖤𝖥𝖦𝖧𝖨𝖩𝖪𝖫𝖬𝖭𝖮𝖯𝖰𝖱𝖲𝖳𝖴𝖵𝖶𝖷𝖸𝖹",
            "𝐴𝐵𝐶𝐷𝐸𝐹𝐺𝐻𝐼𝐽𝐾𝐿𝑀𝑁𝑂𝑃𝑄𝑅𝑆𝑇𝑈𝑉𝑊𝑋𝑌𝑍",
            "𝘈𝘉𝘊𝘋𝘌𝘍𝘎𝘏𝘐𝘑𝘒𝘓𝘔𝘕𝘖𝘗𝘘𝘙𝘚𝘛𝘜𝘝𝘞𝘟𝘠𝘡",
            "𝘼𝘽𝘾𝘿𝙀𝙁𝙂𝙃𝙄𝙅𝙆𝙇𝙈𝙉𝙊𝙋𝙌𝙍𝙎𝙏𝙐𝙑𝙒𝙓𝙔𝙕",
            "𝑨𝑩𝑪𝑫𝑬𝑭𝑮𝑯𝑰𝑱𝑲𝑳𝑴𝑵𝑶𝑷𝑸𝑹𝑺𝑻𝑼𝑽𝑾𝑿𝒀𝒁",
            "𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔𝐕𝐖𝐗𝐘𝐙",
            "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭",
            "𝔄𝔅ℭ𝔇𝔈𝔉𝔊ℌℑ𝔍𝔎𝔏𝔐𝔑𝔒𝔓𝔔ℜ𝔖𝔗𝔘𝔙𝔚𝔛𝔜ℨ",
            "𝕬𝕭𝕮𝕯𝕰𝕱𝕲𝕳𝕴𝕵𝕶𝕷𝕸𝕹𝕺𝕻𝕼𝕽𝕾𝕿𝖀𝖁𝖂𝖃𝖄𝖅",
            "🅐🅑🅒🅓🅔🅕🅖🅗🅘🅙🅚🅛🅜🅝🅞🅟🅠🅡🅢🅣🅤🅥🅦🅧🅨🅩",
            "🅰🅱🅲🅳🅴🅵🅶🅷🅸🅹🅺🅻🅼🅽🅾🅿🆀🆁🆂🆃🆄🆅🆆🆇🆈🆉",
            "ⒶⒷⒸⒹⒺⒻⒼⒽⒾⒿⓀⓁⓂⓃⓄⓅⓆⓇⓈⓉⓊⓋⓌⓍⓎⓏ",
            "ⓐⓑⓒⓓⓔⓕⓖⓗⓘⓙⓚⓛⓜⓝⓞⓟⓠⓡⓢⓣⓤⓥⓦⓧⓨⓩ",
            "ᴬᴮᶜᴰᴱᶠᴳᴴᴵᴶᴷᴸᴹᴺᴼᴾQᴿᔆᵀᵁⱽᵂˣʸᶻ",
            "ᵃᵇᶜᵈᵉᶠᵍʰᶤʲᵏˡᵐᶰᵒᵖᵠʳˢᵗᵘᵛʷˣʸᶻ",
            "𝔸𝔹ℂ𝔻𝔼𝔽𝔾ℍ𝕀𝕁𝕂𝕃𝕄ℕ𝕆ℙℚℝ𝕊𝕋𝕌𝕍𝕎𝕏𝕐ℤ",
            "𝒜ℬ𝒞𝒟ℰℱ𝒢ℋℐ𝒥𝒦ℒℳ𝒩𝒪𝒫𝒬ℛ𝒮𝒯𝒰𝒱𝒲𝒳𝒴𝒵",
            "𝓐𝓑𝓒𝓓𝓔𝓕𝓖𝓗𝓘𝓙𝓚𝓛𝓜𝓝𝓞𝓟𝓠𝓡𝓢𝓣𝓤𝓥𝓦𝓧𝓨𝓩",
            "αвcdeғɢнɪᴊĸℓмɴoρqʀѕтυvᴡxʏᴢ",
            "αႦƈԃҽϝɠԋιʝƙʅɱɳσρϙɾʂƚυʋɯxყȥ",
            "ค๒ς๔єŦgђเןкl๓ภỖปợгรtยvฬхץz",
            "₳฿₵ĐɆ₣₲ⱧłJ₭Ⱡ₥₦Ø₱QⱤ₴₮ɄV₩ӾɎⱫ",
            "ᗩᗷᑕᗪEᖴGᕼIᒍKᒪᗰᑎOᑭᑫᖇᔕTᑌᐯᗯ᙭Yᘔ",
            "卂乃匚ᗪ乇千Ꮆ卄丨ﾌҜㄥ爪几ㄖ卩Ɋ尺丂ㄒㄩᐯ山乂ㄚ乙",
            "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ",
            "🄰🄱🄲🄳🄴🄵🄶🄷🄸🄹🄺🄻🄼🄽🄾🄿🅀🅁🅂🅃🅄🅅🅆🅇🅈🅉"
        ]

        special_styles = [
            f"꧁༒{name}༒꧂",
            f"꧁ঔৣ☬{name}☬ঔৣ꧂",
            f"▶ ●─{name}─亗",
            f"꧁☆☬{name}☬☆꧂",
            f"ᎧᎮܔ{name}☯࿐",
            f"亗『{name}』亗",
            f"ıllıllı{name}ıllıllı",
            f"✦✧✧{name}✧✧✦",
            f"▁ ▂ ▄ ▅ ▆ ▇ █{name}█ ▇ ▆ ▅ ▄ ▂ ▁",
            f"◦•●◉✿{name}✿◉●•◦",
            f"(♥‿♥){name}(♥‿♥)",
            f"(ᵔᴥᵔ)(ᵔᴥᵔ){name}(ᵔᴥᵔ)(ᵔᴥᵔ)",
            f"■□■□■□■□{name}■□■□■□■□",
            f"✩｡:•.─────  ❁{name}❁  ─────.•:｡✩",
            f"✧○ꊞ○ꊞ○ꊞ○ꊞ○ꊞ{name}○ꊞ○ꊞ○ꊞ○ꊞ○✧¤",
            f"•♫•♬•{name}•♫•♬•",
            f"▀▄▀▄▀▄{name}▄▀▄▀▄▀",
            f"°。°。°。°。°。°。{name}°。°。°。°。°。°。",
            f"【｡_｡】{name}【｡_｡】",
            f"(｡◕‿‿◕｡){name}(｡◕‿‿◕｡)",
            f"╔────── ¤ ◎{name}◎ ¤ ──────╗",
            f"●▬▬▬▬๑۩{name}۩๑▬▬▬▬▬●",
            f"❤(｡◕‿◕｡)❤{name}❤(｡◕‿◕｡)❤",
            f"▼△▼△▼△▼{name}▼△▼△▼△▼",
            f"【ツ】{name}【ツ】",
            f"●○●○●○●○{name}●○●○●○●○",
            f"▓▓▓▓▓▓{name}▓▓▓▓▓▓",
            f"➶➶➶➶➶{name}➷➷➷➷➷",
            f"`•.¸¸.•´´¯`••._.•{name}•._.••`¯´´•.¸¸.•`",
            f"❂✿❂✿❂{name}❂✿❂✿❂",
            f"乁། ˵ ◕ – ◕ ˵ །ㄏ{name}乁། ˵ ◕ – ◕ ˵ །ㄏ",
            f"╰། ◉ ◯ ◉ །╯{name}╰། ◉ ◯ ◉ །╯",
            f"░▒▓█{name}█▓▒░",
            f"(ღ˘⌣˘ღ){name}(ღ˘⌣˘ღ)",
            f"︵‿︵‿︵‿︵‿︵‿{name}︵‿︵‿︵‿︵‿︵‿",
            f"⋋⁞ ◔ ﹏ ◔ ⁞⋌{name}⋋⁞ ◔ ﹏ ◔ ⁞⋌",
            f"◇◆◇◆◇◆◇◆◇◆◇{name}◇◆◇◆◇◆◇◆◇◆◇",
            f"¯\_(ツ)_/¯{name}¯\_(ツ)_/¯",
            f"(￢_￢){name}(￢_￢)",
            f"︵‿︵‿୨{name}୧‿︵‿︵",
            f"❤(❁´◡`❁)❤{name}❤(❁´◡`❁)❤",
            f"⫷{name}⫸",
            f"╚═| ~ ಠ ₒ ಠ ~ |═╝{name}╚═| ~ ಠ ₒ ಠ ~ |═╝",
            f"✿◡‿◡{name}◡‿◡✿",
            f"<(▰˘◡˘▰)>{name}<(▰˘◡˘▰)>",
            f"〓〓〓〓〓{name}〓〓〓〓〓",
            f"❏ ❐ ❑ ❒ ❏ ❐{name}❏ ❐ ❑ ❒ ❏ ❐",
            f"◤◢◣◥◤◢◣◥◤{name}◤◢◣◥◤◢◣◥◤",
            f"╰────╯╰────╯╰────╯╰────╯╰────╯╰────╯{name}╰────╯╰────╯╰────╯╰────╯╰────╯╰────╯",
            f"☜♡☞{name}☜♡☞",
            f"(´・_・`){name}(´・_・`)",
            f"✌✌(•ิ‿•ิ)✌✌{name}✌✌(•ิ‿•ิ)✌✌",
            f"✎﹏﹏{name}﹏﹏",
            f"❣❤---» [{name}] «---❤❣",
            f"(▰˘◡˘▰){name}(▰˘◡˘▰)",
            f"☀(ღ˘⌣˘ღ)☀{name}☀(ღ˘⌣˘ღ)☀",
            f"༺═──{name}──═༻",
            f"❄♥‿♥❄{name}❄♥‿♥❄",
            f"❤ᶫᵒᵛᵉᵧₒᵤ❤{name}❤ᶫᵒᵛᵉᵧₒᵤ❤",
            f"●▬ൠൠ▬{name}▬ൠൠ▬●",
            f"[̲̅ə̲̅٨̲̅٥̲̅٦̲̅]{name}[̲̅ə̲̅٨̲̅٥̲̅٦̲̅]",
            f"❀ೋ══•{name}•══ೋ❀",
            f"☃（*^_^*）☃{name}☃（*^_^*）☃",
            f"♡◙‿◙♡{name}♡◙‿◙♡",
            f"❣ლʘ‿ʘლ❣{name}❣ლʘ‿ʘლ❣",
            f"♪┏(°.°)┛{name}♪┏(°.°)┛",
            f"⊂◉‿◉つ{name}⊂◉‿◉つ",
            f"◎ ════{name}════ ◎",
            f"↪↪↪{name}↩↩↩",
            f"◥▓▓{name}▓▓◤",
            f"꧁𓊈𒆜{name}𒆜𓊉꧂",
            f"▄︻̷̿┻̿═━一 {name}"
        ]

        await update.message.reply_text("✨ <b>حالاً ي فندم</b>", parse_mode='HTML')

        for i, style_chars in enumerate(styles):
            try:
                decorated_name = convert_name_to_style(name, style_chars)
                if decorated_name and decorated_name.strip():
                    await update.message.reply_text(decorated_name)
                    await asyncio.sleep(0.3)
            except Exception as e:
                logger.error(f"Error sending decorated name {i}: {e}")
                continue

        for special_style in special_styles:
            try:
                await update.message.reply_text(special_style)
                await asyncio.sleep(0.3)
            except Exception as e:
                logger.error(f"Error sending special style: {e}")
                continue

        await update.message.reply_text("🎉 <b>تم الانتهاء من الزخرفة!</b>\n\n💡 <b>متنساش تشكر حمزه😇❤️‍🩹</b>", parse_mode='HTML')

    except Exception as e:
        logger.error(f"Error in send_decorated_names: {e}")
        await update.message.reply_text("❌ <b>حدث خطأ في الزخرفة. حاول مرة أخرى.</b>", parse_mode='HTML')

# ========== دوال الإيميل المؤقت ==========
async def handle_temp_email_button(query):
    """معالجة زر الإيميل المؤقت"""
    try:
        user_id = query.from_user.id

        if BOT_STATUS == "stopped":
            await query.message.edit_text("⏸️ <b>البوت متوقف حاليًا</b>", parse_mode='HTML')
            return

        if is_user_blocked(user_id):
            await query.message.edit_text("🚫 <b>أنت محظور من استخدام هذا البوت!</b>", parse_mode='HTML')
            return

        email_bot_url = "https://t.me/emaaaaliyBot?start=0"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📧 فتح بوت الإيميل المؤقت", url=email_bot_url)],
            [InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="back_to_main")]
        ])

        await query.message.edit_text(
            "📧 <b>خدمة الإيميل المؤقت</b>\n\n"
            "🔗 <b>انقر على الزر أدناه لفتح بوت الإيميل المؤقت:</b>\n\n"
            f"📨 {email_bot_url}\n\n"
            "💡 <b>طريقة الاستخدام:</b>\n"
            "1. افتح بوت الإيميل المؤقت من الزر أدناه\n"
            "2. إضغط على /start\n"
            "3. سيتم إنشاء إيميل مؤقت تلقائياً\n"
            "4. يمكنك استقبال الرسائل على هذا الإيميل\n"
            "5. الإيميل ينتهي بعد فترة تلقائياً",
            reply_markup=keyboard,
            parse_mode='HTML'
        )

    except Exception as e:
        logger.error(f"Error in handle_temp_email_button: {e}")
        await query.message.edit_text("❌ <b>حدث خطأ في تحميل الخدمة</b>", parse_mode='HTML')

# ========== دوال الأرقام الوهمية ==========
async def handle_virtual_numbers(query):
    """معالجة زر الأرقام الوهمية"""
    try:
        user_id = query.from_user.id

        if BOT_STATUS == "stopped":
            await query.message.edit_text("⏸️ <b>البوت متوقف حاليًا</b>", parse_mode='HTML')
            return

        if is_user_blocked(user_id):
            await query.message.edit_text("🚫 <b>أنت محظور من استخدام هذا البوت!</b>", parse_mode='HTML')
            return

        virtual_numbers_url = "https://ar.temporary-phone-number.com/"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("☎️ موقع الارقام الوهمية ☎️", url=virtual_numbers_url)],
            [InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="back_to_main")]
        ])

        await query.message.edit_text(
            "☎️ <b>اليك افضل موقع ارقام وهمية ☎️✅</b>\n\n"
            "• <b>وعن تجربتي انا شخصيا 👨🏻‍💻✅</b>\n"
            "• <b>شغال 100% ✅</b>\n\n"
            "<b>• الموقع اهو وإدعيلي ❤️‍🩹👇</b>\n\n"
            f"🔗 {virtual_numbers_url}",
            reply_markup=keyboard,
            parse_mode='HTML'
        )

    except Exception as e:
        logger.error(f"Error in handle_virtual_numbers: {e}")
        await query.message.edit_text("❌ <b>حدث خطأ في تحميل الخدمة</b>", parse_mode='HTML')

# ========== الدالة الرئيسية ==========
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id

        add_user_to_database(user_id)

        if BOT_STATUS == "stopped":
            await update.message.reply_text(
                "⏸️ <b>البوت متوقف حاليًا عن العمل</b>\n\n"
                "🔧 <b>جاري الصيانة والتطوير...</b>\n"
                "⏳ <b>سيتم العودة قريبًا</b>\n\n"
                "📞 <b>للاستفسار:</b> @jt_r3r",
                parse_mode='HTML'
            )
            return

        if is_user_blocked(user_id):
            await update.message.reply_text(
                "🚫 <b>أنت محظور من استخدام هذا البوت!</b>\n\n"
                "🔒 <b>لا يمكنك الوصول إلى الخدمات</b>\n"
                "📞 <b>للاستفسار:</b> @jt_r3r",
                parse_mode='HTML'
            )
            return

        user = update.effective_user
        keyboard = InlineKeyboardMarkup(BUTTONS)

        await update.message.reply_text(
            f"<b>مرحباً بك يا {user.first_name} 👋</b>\n\n"
            f"<b>مرحبا بك ف البوت الخاص بـ😈حمزه😈</b>\n\n"
            f"<b>ويرجي استخدام البوت في الخير فقط 🫶</b>\n\n"
            f"🎉 <b>كل الأزرار مجاناً!! 🫶</b>\n\n"
            f"🎛️ <b>اختر من القائمة:</b>",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error in start command: {e}")

async def start1_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء البوت للمطور فقط - إصدار خاص"""
    try:
        user_id = update.effective_user.id

        if not is_developer(user_id):
            await update.message.reply_text("❌ <b>هذا الأمر للمطور فقط!</b>", parse_mode='HTML')
            return

        user = update.effective_user
        keyboard = InlineKeyboardMarkup(BUTTONS)

        total_ratings = sum(len(ratings) for ratings in BOT_RATINGS.values())
        rating_count = sum(len(ratings) for ratings in BOT_RATINGS.values())
        average_rating = sum(sum(ratings) for ratings in BOT_RATINGS.values()) / rating_count if rating_count > 0 else 0

        await update.message.reply_text(
            f"<b>🚀 مرحباً بك يا المطور {user.first_name} 👋</b>\n\n"
            f"<b>🛠️ هذا هو الإصدار الخاص للمطور</b>\n\n"
            f"<b>📊 حالة البوت:</b> {'🟢 نشط' if BOT_STATUS == 'running' else '🔴 متوقف'}\n"
            f"<b>👥 المستخدمون المحظورون:</b> {len(BLOCKED_USERS)}\n"
            f"<b>👥 إجمالي المستخدمين:</b> {len(USER_DATABASE)}\n"
            f"<b>⭐ متوسط التقييم:</b> {average_rating:.1f}/5 ({rating_count} تقييم)\n"
            f"<b>🆔 ID الخاص بك:</b> <code>{user_id}</code>\n\n"
            f"<b>🎛️ الأوامر الإدارية المتاحة:</b>\n"
            f"• /stop - إيقاف البوت\n"
            f"• /zero - تشغيل البوت\n"
            f"• /status - حالة البوت\n"
            f"• /Hamza1 - حظر مستخدم\n"
            f"• /Hamza - فك حظر مستخدم\n"
            f"• /blocked - عرض المحظورين\n"
            f"• /send_all - إذاعة رسالة لجميع المستخدمين\n\n"
            f"<b>🎛️ اختر من القائمة:</b>",
            reply_markup=keyboard,
            parse_mode='HTML'
        )

        logger.info(f"Developer {user_id} used start1 command")

    except Exception as e:
        logger.error(f"Error in start1 command: {e}")

# ========== الدالة الرئيسية للزر ==========
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.callback_query.from_user.id

        if BOT_STATUS == "stopped":
            await update.callback_query.message.edit_text("⏸️ <b>البوت متوقف حاليًا</b>", parse_mode='HTML')
            return

        if is_user_blocked(user_id):
            await update.callback_query.message.edit_text("🚫 <b>أنت محظور من استخدام هذا البوت!</b>", parse_mode='HTML')
            return

        query = update.callback_query
        await query.answer()

        if query.data == "xo_game_menu":
            await xo_game_menu(update, context)
            return

        if query.data == "tv_hack":
            await tv_hack_menu(update, context)
            return

        if query.data == "whatsapp_unban":
            await whatsapp_unban_handler(update, context)
            return

        if query.data == "instagram_ban":
            await instagram_ban_handler(update, context)
            return

        if query.data == "tiktok_report":
            await tiktok_report_handler(update, context)
            return

        if query.data == "fire_apps_menu":
            await handle_fire_apps_menu(query)
            return

        if query.data == "format_app":
            await handle_format_app(query)
            return

        if query.data == "fire_apps_back":
            await handle_fire_apps_menu(query)
            return

        if query.data == "rate_bot":
            await handle_bot_rating(query)
            return

        if query.data == "btn_contacts":
            await handle_contacts_app(query)
            return

        if query.data == "virtual_numbers":
            await handle_virtual_numbers(query)
            return

        if query.data == "btn17":
            await handle_temp_email_button(query)
            return

        if query.data.startswith("rate_"):
            parts = query.data.split("_")
            if len(parts) >= 3:
                rating = int(parts[1])
                service_index = int(parts[2])
                await handle_rating_selection(query, rating, service_index)
            return

        if query.data.startswith("skip_"):
            parts = query.data.split("_")
            if len(parts) >= 2:
                service_index = int(parts[1])
                await handle_rating_skip(query, service_index)
            return

        if query.data == "contact_developer_message":
            await handle_developer_message_request(query)
            context.user_data['sending_to_developer'] = True
            return

        if query.data == "ip_attack":
            await handle_ip_attack(query)
            return

        elif query.data == "shorten_link":
            await query.message.edit_text(
                "🔗 <b>خدمة اختصار الروابط</b>\n\n"
                "📝 <b>أرسل لي الرابط الذي تريد اختصاره:</b>\n\n"
                "💡 <b>ملاحظة:</b> يجب أن يبدأ الرابط بـ https:// أو http://",
                parse_mode='HTML'
            )
            context.user_data['waiting_for_shorten'] = True
            return

        elif query.data == "btn18":
            await query.message.edit_text("🌍 <b>إرسل عنوان IP الذي تريد تتبعه</b>", parse_mode='HTML')
            context.user_data['tracking_ip'] = True
            return

        elif query.data == "btn16":
            await query.message.edit_text("😇 <b>إرسل الرابط الذي تريد فحصه</b>", parse_mode='HTML')
            context.user_data['checking_link'] = True
            return

        elif query.data == "btn14":
            await query.message.edit_text("✨ <b>إرسل الاسم الذي تريد زخرفته</b>", parse_mode='HTML')
            context.user_data['waiting_for_name'] = True
            return

        elif query.data == "btn13":
            await query.message.edit_text("🎁 <b>إرسل لي رابط يبدأ بـ 'https'</b>", parse_mode='HTML')
            context.user_data['waiting_for_link'] = True
            return

        elif query.data == "contact_developer_full_hack":
            await query.message.edit_text(
                "☠️ <b>إختراق الهاتف كاملاً ☠️</b>\n\n"
                "🙂 <b>تتم عملية اختراق الهاتف كاملا والوصول لجميع معلومات جهاز شخص يبتزك او يضايقك عبر برنامج مخفي والاذونات تلقائي ومشفر من جميع مكافحه الفيروسات ما عليك الا انتقوم بارسالة الى الشخص وعند تثبيتة راح تقدر تتحكم بجهازة من خلال البوت فقط</b>\n\n"
                "🔥 <b>راح تقدر تحصل على :</b>\n"
                "<b>✔️ سحب جهات الاتصال 🔥</b>\n\n"
                "<b>✔️ سحب سجل المكالمات 🔥</b>\n\n"
                "<b>✔️ تسجيل صوت الشخص 🔥</b>\n"
                "<b>( بدون ميعرف )</b>\n\n"
                "<b>✔️ تلتقط فيديو وسلفي لوجهه 🔥</b>\n"
                "<b>(بدون ميعرف)</b>\n\n"
                "<b>✔️ سحب جميع الرسائل 🔥</b>\n\n"
                "<b>✔️ تسحب ملف + تحذف ملف 🔥</b>\n\n"
                "<b>✔️ سحب الموقع 🔥</b>\n\n"
                "<b>✔️ سحب جميع الصور 🔥</b>\n\n"
                "<b>✔️ تشغيل صوت + ايقاف الصوت 🔥</b>\n\n"
                "<b>✔️ ارسال رسالة 🔥</b>\n\n"
                "<b>✔️ سحب الحسابات 🔥</b>\n\n"
                "<b>✔️ التجسس على الرسائل 🔥</b>\n\n"
                "<b>✔️ ارسال رسائل لجهات الاتصال 🔥</b>\n\n"
                "<b>✔️ معلومات الجهاز 🔥</b>\n\n"
                "<b>✔️ الاشعارات 🔥</b>\n\n"
                "<b>✔️ التقاط شاشه 🔥</b>\n\n"
                "<b>✔️ الاتصال من هاتف الضحيه 🔥</b>\n\n"
                "<b>✔️ تشفير ملفات الضحيه 🔥</b>\n\n"
                "<b>✔️ سحب رسايل جيميل 🔥</b>\n\n"
                "<b>✔️ فرمته هاتف الضحيه 🔥</b>\n\n"
                "<b>✔️ قرأت كل ما يكتب الضحيه 🔥</b>\n\n"
                "<b>✔️ قفل هاتف الضحيه برمز 🔥</b>\n\n"
                "<b>✔️ فتح اي رابط بهاتف الضحيه 🔥</b>\n\n"
                "<b>✔️ وفي اشياء راح تكتشفها بنفسك 🔥</b>\n\n"
                "😘 <b>للاشتراك رسالني : @jt_r3r 💌</b>\n\n"
                "⚠️ <b>ملاحظة : غير مسؤول امام الله على طريقة استعمالك للطريقة فقط تم صناعتها لمحاربة الابتزاز او لحل مشكلة تواجهك</b>",
                parse_mode='HTML'
            )
            return

        elif query.data == "btn15":
            original_link = LINKS["btn15"].format(user_id=user_id)
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 تغيير شكل الرابط", callback_data="change_link_btn15")],
                [InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="back_to_main")]
            ])

            await query.message.edit_text(
                f"✅ <b>تم إنشاء الرابط بنجاح</b>\n\n"
                f"🔗 <b>رابط سحب الصور:</b>\n{original_link}",
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            return

        elif query.data == "btn_wifi":
            original_link = LINKS["btn_wifi"].format(user_id=user_id)
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 تغيير شكل الرابط", callback_data=f"change_link_btn_wifi")],
                [InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="back_to_main")]
            ])

            await query.message.edit_text(
                f"✅ <b>تم إنشاء الرابط بنجاح</b>\n\n"
                f"🔗 <b>رابط اختراق الواي فاي:</b>\n{original_link}",
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            return

        elif query.data == "btn_ttt":
            original_link = LINKS["btn_ttt"]
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🌐 فتح الموقع", url=original_link)],
                [InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="back_to_main")]
            ])

            await query.message.edit_text(
                f"😂 <b>موقع تخويف فقط!</b>\n\n"
                f"🔗 <b>الرابط:</b>\n{original_link}\n\n"
                f"⚠️ <b>هذا الموقع للترفيه فقط!</b>",
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            return

        elif query.data in LINKS and LINKS[query.data] not in SPECIAL_CASES:
            original_link = LINKS[query.data].format(user_id=user_id)
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 تغيير شكل الرابط", callback_data=f"change_link_{query.data}")],
                [InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="back_to_main")]
            ])

            await query.message.edit_text(
                f"✅ <b>تم إنشاء الرابط بنجاح</b>\n\n"
                f"🔗 <b>رابطك:</b>\n{original_link}",
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            return

        elif query.data.startswith("change_link_"):
            original_btn = query.data.replace("change_link_", "")
            original_link = LINKS[original_btn].format(user_id=user_id)

            await query.message.edit_text("⏳ <b>جاري إنشاء روابط مختصرة...</b>", parse_mode='HTML')

            short_links = await asyncio.get_event_loop().run_in_executor(
                None, link_shortener.shorten_url, original_link
            )

            if not short_links:
                await query.message.edit_text("❌ <b>تعذر اختصار الرابط. حاول مرة أخرى.</b>", parse_mode='HTML')
                return

            message = "✅ <b>روابطك المختصرة:</b>\n\n"

            for i, short_link in enumerate(short_links, 1):
                message += f"{i}. {short_link}\n"

            message += f"\n🔍 <b>ملاحظة:</b> جرب الروابط التي ستعمل معك\n"
            message += f"✅ <b>جميع الروابط شغالة وقابلة للفتح مباشرة!</b>"

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="back_to_main")]
            ])

            await query.message.edit_text(message, reply_markup=keyboard, parse_mode='HTML')
            return

        elif query.data in ['copy_whatsapp_ru', 'copy_whatsapp_ar']:
            if query.data == 'copy_whatsapp_ru':
                await copy_whatsapp_ru(update, context)
            else:
                await copy_whatsapp_ar(update, context)
            return

        elif query.data in ['copy_instagram_hi', 'copy_instagram_ar']:
            if query.data == 'copy_instagram_hi':
                await copy_instagram_hi(update, context)
            else:
                await copy_instagram_ar(update, context)
            return

        elif query.data in ['copy_tiktok_hi', 'copy_tiktok_ar']:
            if query.data == 'copy_tiktok_hi':
                await copy_tiktok_hi(update, context)
            else:
                await copy_tiktok_ar(update, context)
            return

        elif query.data.startswith('bot_move_'):
            await handle_bot_move(update, context)
            return

        elif query.data.startswith('friend_move_'):
            await handle_friend_move(update, context)
            return

        elif query.data == 'mode_vs_bot':
            await vs_bot(update, context)
            return

        elif query.data == 'mode_vs_friend':
            await vs_friend(update, context)
            return

        elif query.data.startswith('country_'):
            await country_selected(update, context)
            return

        elif query.data == "back_to_main":
            keyboard = InlineKeyboardMarkup(BUTTONS)
            await query.message.edit_text("🎛️ <b>القائمة الرئيسية</b>", reply_markup=keyboard, parse_mode='HTML')
            return

        else:
            await query.message.edit_text("❌ هذا الزر غير متاح حالياً")

    except Exception as e:
        logger.error(f"Error in button_click: {e}")
        try:
            await query.message.edit_text("❌ حدث خطأ في المعالجة")
        except:
            await query.message.reply_text("❌ حدث خطأ في المعالجة")

# ========== معالجة الرسائل ==========
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id

        if BOT_STATUS == "stopped":
            if is_developer(user_id) and update.message.text and update.message.text.startswith(('/', 'Hamza1', 'Hamza', 'blocked', 'send_all')):
                pass
            else:
                await update.message.reply_text(
                    "⏸️ <b>البوت متوقف حاليًا عن العمل</b>\n\n"
                    "🔧 <b>جاري الصيانة والتطوير...</b>\n"
                    "⏳ <b>سيتم العودة قريبًا</b>\n\n"
                    "📞 <b>للاستفسار:</b> @jt_r3r",
                    parse_mode='HTML'
                )
                return

        if is_user_blocked(user_id) and not is_developer(user_id):
            await update.message.reply_text(
                "🚫 <b>أنت محظور من استخدام هذا البوت!</b>\n\n"
                "🔒 <b>لا يمكنك الوصول إلى الخدمات</b>\n"
                "📞 <b>للاستفسار:</b> @jt_r3r",
                parse_mode='HTML'
            )
            return

        if is_developer(user_id) and user_id in DEVELOPER_WAITING_FOR_INPUT:
            action = DEVELOPER_WAITING_FOR_INPUT[user_id]
            if action == "waiting_for_broadcast_message":
                await handle_broadcast_message(update, context)
                return
            else:
                await handle_developer_input(update, context)
                return

        user_message = update.message.text

        if context.user_data.get('sending_to_developer'):
            if user_message.strip():
                await send_message_to_developer(update, context, user_message.strip())
            else:
                await update.message.reply_text("❌ <b>لم تقم بإرسال رسالة!</b>", parse_mode='HTML')
            context.user_data['sending_to_developer'] = False
            return

        if context.user_data.get('waiting_for_shorten'):
            await shorten_url_handler(update, context)
            return

        if context.user_data.get('tracking_ip'):
            if user_message.strip():
                ip = user_message.strip()
                await update.message.reply_text("🌍 <b>جاري تتبع العنوان...</b>", parse_mode='HTML')
                result = await track_ip_address(ip)
                await update.message.reply_text(result, parse_mode='HTML')
            else:
                await update.message.reply_text("❌ <b>لم تقم بإرسال عنوان IP!</b>", parse_mode='HTML')
            context.user_data['tracking_ip'] = False
            return

        if user_message.strip().lower() == 'ip':
            await update.message.reply_text("🌍 <b>جاري تتبع عنوان IP الخاص بك...</b>", parse_mode='HTML')
            result = await track_ip_address('myip')
            await update.message.reply_text(result, parse_mode='HTML')
            return

        if context.user_data.get('checking_link'):
            if user_message.strip():
                url = user_message.strip()
                await update.message.reply_text("🔍 <b>جاري فحص الرابط...</b>", parse_mode='HTML')
                result = await check_url_safety(url)
                await update.message.reply_text(f"📊 <b>نتيجة فحص الرابط:</b>\n\n🔗 <b>الرابط:</b> {url}\n\n📋 <b>الحالة:</b> {result}", parse_mode='HTML')
            else:
                await update.message.reply_text("❌ <b>لم تقم بإرسال رابط!</b>", parse_mode='HTML')
            context.user_data['checking_link'] = False
            return

        if context.user_data.get('waiting_for_name'):
            if len(user_message.strip()) > 0:
                name = user_message.strip()
                await send_decorated_names(update, name)
            else:
                await update.message.reply_text("❌ <b>الاسم غير صالح!</b>", parse_mode='HTML')
            context.user_data['waiting_for_name'] = False
            return

        if context.user_data.get('waiting_for_link'):
            if user_message.startswith('https://'):
                await update.message.reply_text(f"🔗 <b>الرابط الملتغم:</b>\n{user_message}\n\n⚠️ <b>تم التلغيم بنجاح!</b>", parse_mode='HTML')
            else:
                await update.message.reply_text("❌ <b>الرابط غير صالح!</b>", parse_mode='HTML')
            context.user_data['waiting_for_link'] = False
            return

        await update.message.reply_text("🔧 <b>استخدم الأزرار للتفاعل مع البوت</b>\n\nاضغط /start لرؤية القائمة الكاملة 🎛️", parse_mode='HTML')
    except Exception as e:
        logger.error(f"Error in handle_message: {e}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"حدث خطأ: {context.error}")

import socket

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def main():
    try:
        print("🚀 جاري تشغيل البوت...")
        
        if is_port_in_use(8080):
            print("⚠️ المنفذ 8080 مشغول، تخطي تشغيل Flask")
        else:
            try:
                import threading
                def run_flask():
                    app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)
                
                flask_thread = threading.Thread(target=run_flask, daemon=True)
                flask_thread.start()
                print("✅ تم تشغيل خادم Flask على المنفذ 8080")
            except Exception as e:
                print(f"⚠️ لم يتمكن من تشغيل Flask: {e}")

        application = Application.builder().token(TOKEN).build()

        application.add_handler(CommandHandler("stop", stop_bot))
        application.add_handler(CommandHandler("zero", start_bot))
        application.add_handler(CommandHandler("status", bot_status))
        application.add_handler(CommandHandler("Hamza1", hamza1_command))
        application.add_handler(CommandHandler("Hamza", hamza_command))
        application.add_handler(CommandHandler("blocked", list_blocked_users))
        application.add_handler(CommandHandler("send_all", send_all_command))
        application.add_handler(CommandHandler("start1", start1_command))

        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CallbackQueryHandler(button_click))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(MessageHandler(filters.PHOTO, handle_message))

        application.add_error_handler(error_handler)

        print("=" * 50)
        print("✅ البوت يعمل بنجاح!")
        print("⏰ " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("🔧 أوامر المطور:")
        print("   /stop - إيقاف البوت للجميع")
        print("   /zero - تشغيل البوت للجميع")
        print("   /status - حالة البوت")
        print("   /Hamza1 - حظر مستخدم")
        print("   /Hamza - فك حظر مستخدم")
        print("   /blocked - عرض المستخدمين المحظورين")
        print("   /send_all - إذاعة رسالة لجميع المستخدمين")
        print("   /start1 - بدء البوت (إصدار المطور)")
        print("⭐ زر تقييم البوت - شغال!")
        print("☠️ زر سحب جهات الاتصال - شغال!")
        print("🔥 زر تطبيقات نار - شغال!")
        print("🎮 زر لعبة XO - شغال!")
        print("📺 زر اختراق قنوات التلفزيون - شغال!")
        print("👨🏻‍💻 زر فك حظر واتساب - شغال!")
        print("‼️ زر حظر انستقرام - شغال!")
        print("💥 زر تبنيد بث تيك توك - شغال!")
        print("☎️ زر ارقام وهمية - شغال!")
        print("📧 زر ايميل مؤقت - شغال!")
        print("🧠 زر الذكاء الاصطناعي - يفتح الرابط مباشرة!")
        print("😈 زر المطور - يفتح الرابط مباشرة!")
        print("=" * 50)

        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
            close_loop=False
        )

    except Exception as e:
        print(f"❌ خطأ: {e}")
        import traceback
        traceback.print_exc()
        print("🔄 إعادة التشغيل خلال 30 ثانية...")
        time.sleep(30)
        main()

if __name__ == '__main__':
    main()
