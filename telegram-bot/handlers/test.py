from datetime import datetime
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes
from database import get_db_session, TelegramUser, BotSubscription
from services.nettap_api import create_user
from services.force_join import check_user_joined, build_join_keyboard, get_join_message
from keyboards import main_menu_keyboard, phone_request_keyboard, back_to_menu
from config import get_test_plan, BRAND_NAME

async def get_test_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    db = get_db_session()
    brand = BRAND_NAME()
    
    try:
        is_joined, not_joined = await check_user_joined(context.bot, user.id)
        if not is_joined:
            await query.edit_message_text(
                get_join_message(),
                reply_markup=build_join_keyboard(not_joined),
                parse_mode="HTML"
            )
            return
        
        test_plan = await get_test_plan()
        if not test_plan:
            await query.edit_message_text(
                "❌ <b>در حال حاضر پلن تست رایگان غیرفعال است.</b>\n\n"
                "لطفاً از بخش «🛒 خرید اشتراک» یکی از پلن‌های فوق‌العاده ما را تهیه کنید.",
                reply_markup=back_to_menu(),
                parse_mode="HTML"
            )
            return
            
        tg_user = db.query(TelegramUser).filter(TelegramUser.telegram_id == user.id).first()
        
        if tg_user and tg_user.has_used_test:
            existing_sub = db.query(BotSubscription).filter(
                BotSubscription.user_telegram_id == user.id,
                BotSubscription.is_test == True
            ).first()
            
            if existing_sub:
                await query.edit_message_text(
                    f"⚠️ <b>شما قبلاً تست دریافت کرده‌اید</b>\n\n"
                    f"🔗 <b>لینک تست شما:</b>\n<code>{existing_sub.sub_url}</code>\n\n"
                    f"⏱ مدت: {test_plan['duration_minutes']} دقیقه از اولین اتصال\n\n"
                    f"💎 برای اشتراک بلندمدت، از فروشگاه استفاده کنید.",
                    reply_markup=back_to_menu(),
                    parse_mode="HTML"
                )
                return
            else:
                await query.edit_message_text(
                    "❌ <b>شما قبلاً تست دریافت کرده‌اید</b>\n\n"
                    "🛒 برای ادامه استفاده، لطفاً یکی از پلن‌های اشتراک را تهیه کنید.",
                    reply_markup=main_menu_keyboard(),
                    parse_mode="HTML"
                )
                return
        
        if not tg_user.phone_number:
            await query.edit_message_text(
                "📱 <b>احراز هویت</b>\n\n"
                "برای دریافت تست رایگان، ابتدا شماره تلفن خود را ارسال کنید.\n\n"
                "🔒 شماره شما فقط برای جلوگیری از سوءاستفاده استفاده می‌شود.\n\n"
                "برای ارسال، از دکمه زیر استفاده کنید ⬇️",
                parse_mode="HTML"
            )
            await context.bot.send_message(
                chat_id=user.id,
                text="👇 دکمه زیر را بزنید:",
                reply_markup=phone_request_keyboard()
            )
            return
        
        await _create_test_account(update, context, tg_user, test_plan, db)
    finally:
        db.close()

async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    user = update.effective_user
    
    if contact.user_id != user.id:
        await update.message.reply_text(
            "❌ لطفاً شماره <b>خودتان</b> را ارسال کنید.",
            parse_mode="HTML"
        )
        return
    
    phone = contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone
    
    db = get_db_session()
    try:
        existing = db.query(TelegramUser).filter(
            TelegramUser.phone_number == phone,
            TelegramUser.telegram_id != user.id
        ).first()
        
        if existing and existing.has_used_test:
            await update.message.reply_text(
                "❌ <b>این شماره قبلاً برای دریافت تست استفاده شده است</b>\n\n"
                "🛒 برای ادامه، از فروشگاه یکی از پلن‌ها را تهیه کنید.",
                reply_markup=ReplyKeyboardRemove(),
                parse_mode="HTML"
            )
            await update.message.reply_text(
                "منوی اصلی:",
                reply_markup=main_menu_keyboard()
            )
            return
        
        tg_user = db.query(TelegramUser).filter(TelegramUser.telegram_id == user.id).first()
        tg_user.phone_number = phone
        db.commit()
        
        test_plan = await get_test_plan()
        if not test_plan:
            await update.message.reply_text(
                "❌ پلن تست در حال حاضر غیرفعال است.",
                reply_markup=ReplyKeyboardRemove()
            )
            await update.message.reply_text("منوی اصلی:", reply_markup=main_menu_keyboard())
            return
            
        await update.message.reply_text(
            "✅ <b>شماره شما ثبت شد</b>\n\n⏳ در حال ساخت اکانت تست...",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="HTML"
        )
        
        await _create_test_account_from_message(update, context, tg_user, test_plan, db)
    finally:
        db.close()

async def _create_test_account(update: Update, context: ContextTypes.DEFAULT_TYPE, tg_user, test_plan, db):
    query = update.callback_query
    await query.edit_message_text("⏳ در حال ساخت اکانت تست...")
    
    username = f"test_{tg_user.telegram_id}"
    result = await create_user(
        username=username, 
        duration_minutes=test_plan["duration_minutes"],
        group_id=test_plan.get("group_id")
    )
    
    if not result:
        await query.edit_message_text(
            "❌ خطا در ساخت اکانت. لطفاً دوباره تلاش کنید.",
            reply_markup=back_to_menu()
        )
        return
    
    sub_url = result["sub_url"]
    tg_user.has_used_test = True
    tg_user.test_sub_token = result["token"]
    db.commit()
    
    bot_sub = BotSubscription(
        user_telegram_id=tg_user.telegram_id,
        sub_username=username,
        sub_token=result["token"],
        sub_url=sub_url,
        plan_id="test",
        duration_minutes=test_plan["duration_minutes"],
        is_test=True,
        created_at=datetime.utcnow()
    )
    db.add(bot_sub)
    db.commit()
    
    await _send_test_result(context, tg_user.telegram_id, sub_url, test_plan["duration_minutes"], query.message.message_id)

async def _create_test_account_from_message(update: Update, context: ContextTypes.DEFAULT_TYPE, tg_user, test_plan, db):
    username = f"test_{tg_user.telegram_id}"
    result = await create_user(
        username=username, 
        duration_minutes=test_plan["duration_minutes"],
        group_id=test_plan.get("group_id")
    )
    
    if not result:
        await update.message.reply_text(
            "❌ خطا در ساخت اکانت. لطفاً دوباره تلاش کنید.",
            reply_markup=main_menu_keyboard()
        )
        return
    
    sub_url = result["sub_url"]
    tg_user.has_used_test = True
    tg_user.test_sub_token = result["token"]
    db.commit()
    
    bot_sub = BotSubscription(
        user_telegram_id=tg_user.telegram_id,
        sub_username=username,
        sub_token=result["token"],
        sub_url=sub_url,
        plan_id="test",
        duration_minutes=test_plan["duration_minutes"],
        is_test=True,
        created_at=datetime.utcnow()
    )
    db.add(bot_sub)
    db.commit()
    
    await _send_test_result(context, tg_user.telegram_id, sub_url, test_plan["duration_minutes"])

async def _send_test_result(context, chat_id, sub_url, duration, edit_message_id=None):
    brand = BRAND_NAME()
    message = (
        f"🎉 <b>اکانت تست شما آماده است!</b>\n\n"
        f"⏱ <b>مدت:</b> {duration} دقیقه\n"
        f"♾ <b>حجم:</b> نامحدود\n"
        f"🌐 <b>سرورها:</b> اختصاصی\n\n"
        f"🔗 <b>لینک اشتراک شما:</b>\n"
        f"<code>{sub_url}</code>\n\n"
        f"📌 <b>نکات مهم:</b>\n"
        f"1️⃣ زمان اکانت از اولین اتصال شروع می‌شود\n"
        f"2️⃣ برای مشاهده آموزش اتصال، دکمه «📚 آموزش اتصال» را بزنید\n"
        f"3️⃣ برای اشتراک بلندمدت، از فروشگاه {brand} دیدن کنید"
    )
    
    if edit_message_id:
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=edit_message_id,
                text=message,
                reply_markup=main_menu_keyboard(),
                parse_mode="HTML"
            )
            return
        except:
            pass
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=message,
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML"
    )