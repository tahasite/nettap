from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from database import get_db_session, BotSubscription
from services.nettap_api import get_user_by_username
from keyboards import back_to_menu, main_menu_keyboard

def format_time_remaining(expire_date):
    if not expire_date:
        return "🟡 هنوز فعال نشده"
    
    now = datetime.utcnow()
    if isinstance(expire_date, str):
        expire_date = datetime.fromisoformat(expire_date.replace("Z", ""))
    
    if expire_date < now:
        return "🔴 منقضی شده"
    
    diff = expire_date - now
    total_minutes = int(diff.total_seconds() / 60)
    
    if total_minutes >= 1440:
        days = total_minutes // 1440
        hours = (total_minutes % 1440) // 60
        return f"🟢 {days} روز و {hours} ساعت"
    elif total_minutes >= 60:
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"🟡 {hours} ساعت و {minutes} دقیقه"
    else:
        return f"🔴 {total_minutes} دقیقه"

def format_duration(minutes):
    if minutes >= 1440:
        return f"{minutes // 1440} روز"
    elif minutes >= 60:
        return f"{minutes // 60} ساعت"
    else:
        return f"{minutes} دقیقه"

async def my_subs_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("⏳ در حال دریافت اطلاعات...")
    
    user = query.from_user
    db = get_db_session()
    
    try:
        subs = db.query(BotSubscription).filter(
            BotSubscription.user_telegram_id == user.id
        ).order_by(BotSubscription.created_at.desc()).all()
        
        if not subs:
            await query.edit_message_text(
                "📭 <b>هنوز هیچ اشتراکی ندارید</b>\n\n"
                "🎁 برای شروع، اکانت تست رایگان بگیرید\n"
                "🛒 یا از فروشگاه یک پلن انتخاب کنید",
                reply_markup=main_menu_keyboard(),
                parse_mode="HTML"
            )
            return
        
        text = "📊 <b>اشتراک‌های شما</b>\n\n"
        
        for i, sub in enumerate(subs, 1):
            api_user = await get_user_by_username(sub.sub_username)
            
            if not api_user:
                text += f"{i}. ❌ {sub.sub_username} (حذف شده)\n\n"
                continue
            
            expire_date = None
            if api_user.get("expire_date"):
                try:
                    expire_date = datetime.fromisoformat(api_user["expire_date"].replace("Z", ""))
                except:
                    pass
            
            time_status = format_time_remaining(expire_date)
            
            if api_user.get("is_blocked"):
                status_icon = "⛔"
                status_text = "مسدود"
            elif api_user.get("is_active"):
                status_icon = "✅"
                status_text = "فعال"
            else:
                status_icon = "❌"
                status_text = "منقضی"
            
            sub_type = "🎁 تست" if sub.is_test else f"💎 {format_duration(sub.duration_minutes)}"
            
            text += (
                f"<b>{i}. {sub_type}</b>\n"
                f"├ وضعیت: {status_icon} {status_text}\n"
                f"├ زمان: {time_status}\n"
                f"└ لینک: <code>{sub.sub_url}</code>\n\n"
            )
        
        keyboard = [
            [InlineKeyboardButton("🔄 بروزرسانی", callback_data="my_subs")],
            [InlineKeyboardButton("🛒 خرید اشتراک جدید", callback_data="shop")],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
    finally:
        db.close()