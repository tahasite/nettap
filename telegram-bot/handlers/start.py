from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from database import get_db_session, TelegramUser
from services.force_join import check_user_joined, build_join_keyboard, get_join_message
from keyboards import main_menu_keyboard
from config import BRAND_NAME

def get_welcome_message():
    brand = BRAND_NAME()
    return f"""
🛡️ <b>به ربات {brand} خوش آمدید</b>

⚡ سریع‌ترین و امن‌ترین VPN برای دسترسی به اینترنت آزاد

🎁 <b>امکانات ربات:</b>
├ دریافت اکانت تست رایگان
├ خرید اشتراک با قیمت‌های استثنایی
├ مدیریت اشتراک‌های شما
├ آموزش‌های تصویری اتصال
└ پشتیبانی سریع

🔥 <b>یک گزینه را انتخاب کنید:</b>
"""

async def register_user(user, db):
    tg_user = db.query(TelegramUser).filter(TelegramUser.telegram_id == user.id).first()
    
    if not tg_user:
        tg_user = TelegramUser(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow()
        )
        db.add(tg_user)
        db.commit()
        db.refresh(tg_user)
    else:
        tg_user.username = user.username
        tg_user.first_name = user.first_name
        tg_user.last_name = user.last_name
        tg_user.last_activity = datetime.utcnow()
        db.commit()
    
    return tg_user

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = get_db_session()
    
    try:
        tg_user = await register_user(user, db)
        
        if tg_user.is_banned:
            await update.message.reply_text("❌ حساب شما مسدود شده است. برای اطلاعات بیشتر با پشتیبانی تماس بگیرید.")
            return
        
        args = context.args
        if args and args[0].startswith("ref_"):
            try:
                ref_id = int(args[0].replace("ref_", ""))
                if ref_id != user.id and not tg_user.referred_by:
                    tg_user.referred_by = ref_id
                    db.commit()
            except:
                pass
        
        is_joined, not_joined = await check_user_joined(context.bot, user.id)
        
        if not is_joined:
            tg_user.is_joined_channels = False
            db.commit()
            await update.message.reply_text(
                get_join_message(),
                reply_markup=build_join_keyboard(not_joined),
                parse_mode="HTML"
            )
            return
        
        tg_user.is_joined_channels = True
        db.commit()
        
        await update.message.reply_text(
            get_welcome_message(),
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML"
        )
    finally:
        db.close()

async def check_join_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    db = get_db_session()
    
    try:
        await query.answer("🔍 در حال بررسی...")
        
        is_joined, not_joined = await check_user_joined(context.bot, user.id)
        
        if not is_joined:
            await query.answer("❌ هنوز در همه کانال‌ها عضو نشدی!", show_alert=True)
            return
        
        tg_user = db.query(TelegramUser).filter(TelegramUser.telegram_id == user.id).first()
        if tg_user:
            tg_user.is_joined_channels = True
            tg_user.last_activity = datetime.utcnow()
            db.commit()
        
        await query.edit_message_text(
            f"🎉 <b>عالی! عضویت شما تایید شد</b>\n\n{get_welcome_message()}",
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML"
        )
    finally:
        db.close()

async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    db = get_db_session()
    try:
        user = query.from_user
        tg_user = db.query(TelegramUser).filter(TelegramUser.telegram_id == user.id).first()
        if tg_user:
            tg_user.last_activity = datetime.utcnow()
            db.commit()
        
        is_joined, not_joined = await check_user_joined(context.bot, user.id)
        if not is_joined:
            await query.edit_message_text(
                get_join_message(),
                reply_markup=build_join_keyboard(not_joined),
                parse_mode="HTML"
            )
            return
        
        await query.edit_message_text(
            get_welcome_message(),
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML"
        )
    finally:
        db.close()