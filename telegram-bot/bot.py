import logging
import os
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from config import (
    BOT_TOKEN, TELEGRAM_API_PROXY, WEBHOOK_URL, WEBHOOK_LISTEN_PORT, 
    USE_WEBHOOK, BOT_ENABLED, reload_settings
)
from handlers.start import start_handler, check_join_handler, main_menu_handler
from handlers.test import get_test_handler, contact_handler
from handlers.shop import shop_handler, buy_plan_handler, send_receipt_handler, cancel_order_handler, receipt_photo_handler
from handlers.account import my_subs_handler
from handlers.tutorial import tutorial_handler, tutorial_platform_handler
from handlers.referral import referral_handler
from handlers.admin import approve_order_handler, reject_order_handler, admin_menu_handler, broadcast_handler, admin_reject_reason_handler
from services.notifier import setup_notifier

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def wait_for_config():
    for attempt in range(30):
        reload_settings()
        token = BOT_TOKEN()
        if token and len(token) > 20:
            if not BOT_ENABLED():
                logger.warning("⚠️  Bot is disabled in settings. Waiting...")
                time.sleep(10)
                continue
            logger.info(f"✅ Bot token loaded from settings (len: {len(token)})")
            return token
        logger.warning(f"⏳ Waiting for bot token... (attempt {attempt + 1}/30)")
        time.sleep(5)
    logger.error("❌ No bot token configured! Please set it in Admin Panel > Settings > Telegram")
    return None

def main():
    token = wait_for_config()
    if not token:
        logger.error("Bot cannot start without a token. Exiting.")
        return
    
    proxy = TELEGRAM_API_PROXY()
    
    builder = Application.builder().token(token)
    
    if proxy:
        proxy_url = f"{proxy}/bot"
        logger.info(f"🛰️ Using Telegram API Proxy: {proxy_url}")
        builder.base_url(proxy_url)
        
    app = builder.build()
    
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("admin", admin_menu_handler))
    app.add_handler(CommandHandler("broadcast", broadcast_handler))
    app.add_handler(CommandHandler("reload", reload_cmd))
    
    app.add_handler(CallbackQueryHandler(check_join_handler, pattern="^check_join$"))
    app.add_handler(CallbackQueryHandler(main_menu_handler, pattern="^main_menu$"))
    app.add_handler(CallbackQueryHandler(get_test_handler, pattern="^get_test$"))
    app.add_handler(CallbackQueryHandler(shop_handler, pattern="^shop$"))
    app.add_handler(CallbackQueryHandler(buy_plan_handler, pattern="^buy_"))
    app.add_handler(CallbackQueryHandler(send_receipt_handler, pattern="^send_receipt_"))
    app.add_handler(CallbackQueryHandler(cancel_order_handler, pattern="^cancel_order_"))
    app.add_handler(CallbackQueryHandler(my_subs_handler, pattern="^my_subs$"))
    app.add_handler(CallbackQueryHandler(tutorial_handler, pattern="^tutorial$"))
    app.add_handler(CallbackQueryHandler(tutorial_platform_handler, pattern="^tut_"))
    app.add_handler(CallbackQueryHandler(referral_handler, pattern="^referral$"))
    app.add_handler(CallbackQueryHandler(approve_order_handler, pattern="^approve_"))
    app.add_handler(CallbackQueryHandler(reject_order_handler, pattern="^reject_"))
    
    app.add_handler(MessageHandler(filters.CONTACT, contact_handler))
    app.add_handler(MessageHandler(filters.PHOTO, receipt_photo_handler))
    app.add_handler(MessageHandler(filters.TEXT & filters.REPLY, admin_reject_reason_handler))
    
    setup_notifier(app)
    
    webhook_url = WEBHOOK_URL()
    
    if USE_WEBHOOK and webhook_url:
        logger.info(f"🚀 Starting bot with WEBHOOK on port {WEBHOOK_LISTEN_PORT}")
        logger.info(f"📡 Webhook URL: {webhook_url}")
        app.run_webhook(
            listen="127.0.0.1",
            port=WEBHOOK_LISTEN_PORT,
            url_path=token,
            webhook_url=f"{webhook_url}/{token}",
            allowed_updates=Update.ALL_TYPES
        )
    else:
        logger.info("🤖 Starting bot with POLLING")
        app.run_polling(allowed_updates=Update.ALL_TYPES)

async def reload_cmd(update, context):
    from config import ADMIN_IDS
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS():
        return
    reload_settings()
    await update.message.reply_text("✅ تنظیمات ربات از پنل بارگذاری مجدد شد.\n\nبرای اعمال تغییرات توکن یا پروکسی، سرویس ربات را ری‌استارت کنید.")

if __name__ == "__main__":
    main()