
import subprocess
import sys
import time
import threading
from flask import Flask, jsonify
import requests

# تثبيت المكتبات المطلوبة تلقائياً
def install_packages():
    required_packages = ['python-telegram-bot', 'flask', 'requests']
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} مثبت بالفعل")
        except ImportError:
            print(f"📦 جاري تثبيت {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ تم تثبيت {package} بنجاح")

# تثبيت المكتبات
install_packages()

# الآن استيراد المكتبات بعد التثبيت
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler
import asyncio

# تمكين التسجيل للتصحيح
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# تعريف مراحل المحادثة
APP_NAME, APP_PHOTO = range(2)

# معرف المطور
DEVELOPER_CHAT_ID = "7305720183"
DEVELOPER_USERNAME = "@jt_r3r"

# بيانات التواصل مع المطور
CONTACT_INFO = f"""
<b>إذا تأخر تسليم التطبيق لك</b>
<b>تواصل مع حمزه: {DEVELOPER_USERNAME}</b>
"""

# إنشاء تطبيق Flask
app = Flask(__name__)

@app.route('/')
def home():
    """الصفحة الرئيسية"""
    return jsonify({
        "status": "online",
        "service": "Telegram Bot",
        "time": time.strftime('%Y-%m-%d %H:%M:%S'),
        "message": "Bot is running!",
        "developer": DEVELOPER_USERNAME
    })

@app.route('/health')
def health_check():
    """فحص صحة البوت"""
    return jsonify({
        "status": "healthy",
        "timestamp": time.time(),
        "uptime": time.strftime('%H:%M:%S')
    })

@app.route('/keepalive')
def keep_alive_endpoint():
    """نقطة نهاية للحفاظ على البوت نشط"""
    return jsonify({
        "message": "Keep-alive triggered",
        "time": time.strftime('%Y-%m-%d %H:%M:%S'),
        "bot": "Active"
    })

def run_flask():
    """تشغيل خادم Flask"""
    app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)

# دالة بدء المحادثة
async def start(update: Update, context: CallbackContext) -> int:
    """يبدأ المحادثة ويرسل الرسالة الأولى."""
    user = update.effective_user
    
    # الرسالة الأولى المعدلة
    welcome_message = """<b>مرحبا بك 👋</b>

<b>1: إرسل الاسم التي تريد التطبيق يظهر به ✅❗</b>
<b>2: إرسل الصوره التي تريد التطبيق يظهر بها ⚡</b>

<b>وسيتم إنشاء تطبيق سحب الصور بنفس المواصفات اللي سترسلها ✅🥰</b>"""
    
    await update.message.reply_text(
        f"{welcome_message}",
        parse_mode='HTML'
    )
    
    # انتظار ثانيتين ثم إرسال الرسالة الثانية
    await asyncio.sleep(2)
    
    # الرسالة الثانية
    await update.message.reply_text(
        "<b>إرسل الآن إسم التطبيق</b>",
        parse_mode='HTML'
    )
    
    return APP_NAME

# دالة لمعرفة الـ ID
async def get_id(update: Update, context: CallbackContext):
    """يرجع الـ ID الخاص بالمستخدم."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    await update.message.reply_text(
        f"<b>👤 معرفك: {user.id}</b>\n"
        f"<b>💬 معرف الدردشة: {chat_id}</b>\n\n"
        f"<b>📝 أرسل المعرف هذا إلى المطور ليرسله في المتغير DEVELOPER_CHAT_ID</b>",
        parse_mode='HTML'
    )

# دالة استقبال اسم التطبيق
async def receive_app_name(update: Update, context: CallbackContext) -> int:
    """يستقبل اسم التطبيق من المستخدم."""
    app_name = update.message.text
    context.user_data['app_name'] = app_name
    
    # حفظ اسم المستخدم ومعلوماته
    user = update.effective_user
    context.user_data['user_name'] = f"{user.first_name} {user.last_name or ''}"
    context.user_data['user_username'] = f"@{user.username}" if user.username else "لا يوجد"
    context.user_data['user_id'] = user.id
    
    await update.message.reply_text(
        "<b>إرسل الآن صورة التطبيق</b>",
        parse_mode='HTML'
    )
    
    return APP_PHOTO

# دالة استقبال صورة التطبيق
async def receive_app_photo(update: Update, context: CallbackContext) -> int:
    """يستقبل صورة التطبيق من المستخدم."""
    user = update.effective_user
    app_name = context.user_data.get('app_name', 'غير محدد')
    user_name = context.user_data.get('user_name', '')
    user_username = context.user_data.get('user_username', '')
    user_id = context.user_data.get('user_id', '')
    
    # الحصول على الصورة
    photo_file = await update.message.photo[-1].get_file()
    
    # تجهيز معلومات الطلب للمطور
    request_info = f"""<b>📋 طلب تطبيق جديد</b>
<b>─────────────────────</b>
<b>👤 المستخدم:</b> <code>{user_name}</code>
<b>🆔 المعرف:</b> <code>{user_username}</code>
<b>📞 ID:</b> <code>{user_id}</code>
<b>─────────────────────</b>
<b>📱 اسم التطبيق:</b> <code>{app_name}</code>
<b>─────────────────────</b>"""
    
    try:
        # إرسال الطلب إلى المطور
        # أولاً: إرسال النص
        await context.bot.send_message(
            chat_id=DEVELOPER_CHAT_ID,
            text=request_info,
            parse_mode='HTML'
        )
        
        # ثانياً: إرسال الصورة
        await context.bot.send_photo(
            chat_id=DEVELOPER_CHAT_ID,
            photo=photo_file.file_id,
            caption=f"<b>صورة لتطبيق:</b> <code>{app_name}</code>",
            parse_mode='HTML'
        )
        
        # رسالة التأكيد للمستخدم
        confirmation_message = f"""<b>✅ تم إرسال طلبك لحمزه</b>

<b>📱 اسم التطبيق:</b> <code>{app_name}</code>

<b>🎯 سيتم إنشاء تطبيق سحب الصور بنفس المواصفات في أقرب وقت ممكن</b>

{CONTACT_INFO}"""
        
        await update.message.reply_text(
            confirmation_message,
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"خطأ في إرسال الطلب للمطور: {e}")
        await update.message.reply_text(
            "<b>❌ حدث خطأ في إرسال طلبك. يرجى المحاولة مرة أخرى لاحقاً.</b>",
            parse_mode='HTML'
        )
    
    # إنهاء المحادثة
    return ConversationHandler.END

# دالة الإلغاء
async def cancel(update: Update, context: CallbackContext) -> int:
    """يلغي المحادثة."""
    await update.message.reply_text(
        "<b>تم إلغاء الطلب. يمكنك البدء مرة أخرى باستخدام /start</b>",
        parse_mode='HTML'
    )
    return ConversationHandler.END

# دالة المساعدة
async def help_command(update: Update, context: CallbackContext):
    """يرسل رسالة المساعدة."""
    help_text = f"""<b>🤖 أوامر البوت:</b>

<b>/start</b> - بدء طلب تطبيق جديد
<b>/id</b> - معرفة رقم ID الخاص بك
<b>/help</b> - عرض هذه الرسالة
<b>/cancel</b> - إلغاء الطلب الحالي

<b>📝 طريقة الاستخدام:</b>
1. أرسل <b>/start</b>
2. أرسل اسم التطبيق
3. أرسل صورة توضيحية للتطبيق
4. سيتم إرسال طلبك للمطور

<b>👨‍💻 المطور:</b> حمزه {DEVELOPER_USERNAME}

<b>🌐 البوت يعمل مع Flask للحفاظ على النشاط</b>"""
    
    await update.message.reply_text(help_text, parse_mode='HTML')

# دالة للحفاظ على البوت نشط باستخدام Flask
def keep_alive_with_flask():
    """تشغيل Flask في thread منفصل"""
    try:
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        print("✅ Flask server started on port 8080")
        print("🌐 Access: http://0.0.0.0:8080")
    except Exception as e:
        print(f"⚠️ خطأ في تشغيل Flask: {e}")

# دالة ذاتية للحفاظ على النشاط
def self_ping():
    """إرسال طلبات ذاتية للحفاظ على البوت نشط"""
    while True:
        try:
            # إرسال طلب إلى نفس الخادم
            response = requests.get('http://0.0.0.0:8080/keepalive', timeout=5)
            print(f"[{time.strftime('%H:%M:%S')}] 🔄 Self-ping sent, Status: {response.status_code}")
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] ⚠️ Self-ping failed: {e}")
        
        # الانتظار 5 دقائق قبل الإرسال التالي
        time.sleep(300)

# دالة لطباعة رسالة التشغيل
def print_banner():
    """طباعة رسالة ترحيبية عند تشغيل البوت"""
    print("\n" + "="*60)
    print("🤖 TELEGRAM BOT STARTED SUCCESSFULLY!")
    print("="*60)
    print(f"⏰ Start Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    print("📦 Installed Packages: python-telegram-bot, flask, requests")
    print("="*60)
    print("📡 Flask Integration for 24/7 Uptime:")
    print("🌐 Web Server: http://0.0.0.0:8080")
    print("❤️ Health Check: http://0.0.0.0:8080/health")
    print("🔗 Keep-alive: http://0.0.0.0:8080/keepalive")
    print("="*60)
    print("💡 To keep bot alive 24/7:")
    print("1. Use UptimeRobot.com (Free)")
    print("2. Set URL: http://0.0.0.0:8080/keepalive")
    print("3. Set interval: 5 minutes")
    print("="*60 + "\n")

# دالة الرئيسية
def main() -> None:
    """تشغيل البوت."""
    # توكن البوت
    TOKEN = "8494446795:AAHMAZFOI-KHtxSwLAxBtShQxd0c5yhnmC4"
    
    # طباعة بانر التشغيل
    print_banner()
    
    # تشغيل Flask في thread منفصل
    keep_alive_with_flask()
    
    # انتظار قليل لبدء Flask
    time.sleep(2)
    
    # بدء نظام self-ping
    self_ping_thread = threading.Thread(target=self_ping, daemon=True)
    self_ping_thread.start()
    
    # إنشاء تطبيق Telegram
    application = Application.builder().token(TOKEN).build()
    
    # إعداد معالج المحادثة
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            APP_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_app_name)
            ],
            APP_PHOTO: [
                MessageHandler(filters.PHOTO, receive_app_photo)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    # إضافة المعالجات
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("id", get_id))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cancel", cancel))
    
    print("✅ Telegram bot started successfully!")
    print("📱 Send /start to the bot to begin")
    print("🔄 Auto keep-alive enabled with self-ping every 5 minutes")
    print("⚡ Bot is now ready to receive requests!")
    
    # تشغيل البوت
    application.run_polling()

if __name__ == '__main__':
    main()
