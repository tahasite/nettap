from telegram import Update
from telegram.ext import ContextTypes
from database import get_db_session, TelegramUser
from keyboards import back_to_menu
from config import BRAND_NAME

async def referral_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    brand = BRAND_NAME()
    bot_info = await context.bot.get_me()
    bot_username = bot_info.username
    
    db = get_db_session()
    try:
        tg_user = db.query(TelegramUser).filter(TelegramUser.telegram_id == user.id).first()
        if not tg_user:
            await query.edit_message_text("❌ خطا در بارگذاری حساب کاربری.", reply_markup=back_to_menu())
            return
            
        referrals_count = db.query(TelegramUser).filter(TelegramUser.referred_by == user.id).count()
        ref_link = f"https://t.me/{bot_username}?start=ref_{user.id}"
        
        text = (
            f"🔗 <b>سیستم معرفی به دوستان (کسب درآمد)</b>\n\n"
            f"با دعوت دوستان خود به ربات {brand}، به میزان <b>۲۰٪</b> از مبلغ هر خرید آن‌ها را به عنوان اعتبار هدیه دریافت کنید! 🎁\n\n"
            f"📊 <b>آمار دعوت‌های شما:</b>\n"
            f"├ تعداد زیرمجموعه‌ها: {referrals_count} نفر\n"
            f"└ کیف پول شما: <b>{tg_user.balance:,} تومان</b>\n\n"
            f"📥 <b>لینک دعوت اختصاصی شما:</b>\n"
            f"<code>{ref_link}</code>\n\n"
            f"💡 <b>راهنما:</b> لینک بالا را برای دوستان خود بفرستید. هر زمان دوستی با این لینک وارد ربات شود و خریدی انجام دهد، معادل ۲۰٪ کل مبلغ به موجودی کیف پول شما واریز خواهد شد که از آن می‌توانید برای تمدید اشتراک یا خرید اکانت استفاده کنید."
        )
        
        await query.edit_message_text(
            text,
            reply_markup=back_to_menu(),
            parse_mode="HTML"
        )
    finally:
        db.close()