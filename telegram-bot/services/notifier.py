import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from telegram.ext import Application
from database import get_db_session, BotSubscription
from services.nettap_api import get_user_by_username

async def check_expirations_task(app: Application):
    db = get_db_session()
    try:
        subs = db.query(BotSubscription).filter(
            BotSubscription.is_test == False,
            BotSubscription.expire_notified == False
        ).all()
        
        now = datetime.utcnow()
        
        for sub in subs:
            api_user = await get_user_by_username(sub.sub_username)
            if not api_user or not api_user.get("expire_date"):
                continue
                
            try:
                expire_date = datetime.fromisoformat(api_user["expire_date"].replace("Z", ""))
            except:
                continue
                
            diff = expire_date - now
            
            if diff <= timedelta(hours=24) and diff > timedelta(seconds=0):
                sub.expire_notified = True
                db.commit()
                
                msg = (
                    f"⚠️ <b>هشدار تمدید اشتراک</b>\n\n"
                    f"مشترک گرامی، اشتراک شما کمتر از <b>۲۴ ساعت</b> دیگر به پایان می‌رسد.\n\n"
                    f"برای جلوگیری از قطع شدن اتصال و حفظ تنظیمات فعلی، همین حالا می‌توانید از بخش «🛒 خرید اشتراک» اقدام به تمدید کنید."
                )
                try:
                    await app.bot.send_message(
                        chat_id=sub.user_telegram_id,
                        text=msg,
                        parse_mode="HTML"
                    )
                except:
                    pass
    except Exception as e:
        print(f"Error in check_expirations_task: {e}")
    finally:
        db.close()

def setup_notifier(app: Application):
    scheduler = BackgroundScheduler()
    
    def run_async_job():
        try:
            loop = asyncio.get_event_loop()
            asyncio.run_coroutine_threadsafe(check_expirations_task(app), loop)
        except:
            pass
        
    scheduler.add_job(run_async_job, "interval", minutes=30)
    scheduler.start()