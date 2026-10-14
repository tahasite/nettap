from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from database import get_db_session, TelegramUser, Order, BotSubscription
from config import CARD_NUMBER, CARD_HOLDER, ADMIN_IDS, BRAND_NAME, get_shop_plans, get_plan_by_key
from keyboards import shop_keyboard, payment_keyboard, back_to_menu, main_menu_keyboard, admin_order_keyboard
from services.force_join import check_user_joined, build_join_keyboard, get_join_message

async def shop_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    is_joined, not_joined = await check_user_joined(context.bot, user.id)
    if not is_joined:
        await query.edit_message_text(
            get_join_message(),
            reply_markup=build_join_keyboard(not_joined),
            parse_mode="HTML"
        )
        return
        
    plans = await get_shop_plans()
    if not plans:
        await query.edit_message_text(
            "❌ <b>فروشگاه موقتاً غیرفعال است.</b>",
            reply_markup=back_to_menu(),
            parse_mode="HTML"
        )
        return
    
    brand = BRAND_NAME()
    text = (
        f"🛒 <b>فروشگاه {brand}</b>\n\n"
        f"⚡ سرعت بالا • 🌍 سرورهای متنوع • ♾ حجم نامحدود\n\n"
        f"💎 <b>ویژگی‌های همه پلن‌ها:</b>\n"
        f"├ اتصال به تمام کشورها\n"
        f"├ حجم کاملاً نامحدود\n"
        f"├ زمان از اولین اتصال شروع می‌شود\n"
        f"├ پشتیبانی از تمام دستگاه‌ها\n"
        f"└ پشتیبانی ۲۴ ساعته\n\n"
        f"🔥 <b>پلن مورد نظر خود را انتخاب کنید:</b>"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=shop_keyboard(plans),
        parse_mode="HTML"
    )

async def buy_plan_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    plan_key = query.data.replace("buy_", "")
    plan = await get_plan_by_key(plan_key)
    
    if not plan:
        await query.edit_message_text("❌ پلن نامعتبر", reply_markup=back_to_menu())
        return
    
    user = query.from_user
    db = get_db_session()
    card_number = CARD_NUMBER()
    card_holder = CARD_HOLDER()
    
    if not card_number or not card_holder:
        await query.edit_message_text(
            "⚠️ <b>سیستم پرداخت تنظیم نشده</b>\n\n"
            "لطفاً با پشتیبانی تماس بگیرید.",
            reply_markup=back_to_menu(),
            parse_mode="HTML"
        )
        return
    
    try:
        pending_order = db.query(Order).filter(
            Order.user_telegram_id == user.id,
            Order.status == "pending"
        ).first()
        
        if pending_order:
            await query.edit_message_text(
                f"⚠️ <b>شما یک سفارش در حال بررسی دارید</b>\n\n"
                f"📦 پلن: {pending_order.plan_name}\n"
                f"💰 مبلغ: {pending_order.plan_price:,} تومان\n"
                f"📅 تاریخ: {pending_order.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
                f"لطفاً منتظر تایید یا رد سفارش قبلی باشید.",
                reply_markup=payment_keyboard(pending_order.id),
                parse_mode="HTML"
            )
            return
        
        order = Order(
            user_telegram_id=user.id,
            plan_id=plan["plan_key"],
            plan_name=plan["name"],
            plan_minutes=plan["duration_minutes"],
            plan_price=plan["price"],
            status="awaiting_payment",
            created_at=datetime.utcnow()
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        
        text = (
            f"🛒 <b>ثبت سفارش</b>\n\n"
            f"📦 <b>پلن:</b> {plan['name']}\n"
            f"💰 <b>مبلغ:</b> <code>{plan['price']:,}</code> تومان\n"
            f"🆔 <b>شماره سفارش:</b> <code>#{order.id}</code>\n\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"💳 <b>اطلاعات پرداخت:</b>\n\n"
            f"شماره کارت:\n"
            f"<code>{card_number}</code>\n\n"
            f"به نام: <b>{card_holder}</b>\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"📝 <b>مراحل خرید:</b>\n"
            f"1️⃣ دقیقاً مبلغ <b>{plan['price']:,} تومان</b> را کارت به کارت کنید\n"
            f"2️⃣ روی دکمه «📤 ارسال رسید پرداخت» بزنید\n"
            f"3️⃣ عکس رسید را ارسال کنید\n"
            f"4️⃣ منتظر تایید ادمین باشید (معمولاً کمتر از ۱ ساعت)\n\n"
            f"⚠️ <b>مهم:</b> حتماً دقیقاً همین مبلغ را واریز کنید"
        )
        
        await query.edit_message_text(
            text,
            reply_markup=payment_keyboard(order.id),
            parse_mode="HTML"
        )
    finally:
        db.close()

async def send_receipt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    order_id = int(query.data.replace("send_receipt_", ""))
    context.user_data["waiting_receipt_for"] = order_id
    
    await query.edit_message_text(
        f"📤 <b>ارسال رسید پرداخت</b>\n\n"
        f"لطفاً <b>عکس رسید</b> یا اسکرین‌شات پرداخت را ارسال کنید.\n\n"
        f"🆔 شماره سفارش: <code>#{order_id}</code>\n\n"
        f"⚠️ فقط عکس ارسال کنید (نه فایل)",
        parse_mode="HTML"
    )

async def receipt_photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    order_id = context.user_data.get("waiting_receipt_for")
    if not order_id:
        return
    
    user = update.effective_user
    db = get_db_session()
    admin_ids = ADMIN_IDS()
    
    try:
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.user_telegram_id == user.id
        ).first()
        
        if not order:
            await update.message.reply_text("❌ سفارش نامعتبر")
            return
        
        if order.status not in ["awaiting_payment", "pending"]:
            await update.message.reply_text("❌ این سفارش دیگر قابل پرداخت نیست")
            return
        
        photo = update.message.photo[-1]
        file_id = photo.file_id
        
        order.receipt_file_id = file_id
        order.receipt_message_id = update.message.message_id
        order.status = "pending"
        db.commit()
        
        context.user_data.pop("waiting_receipt_for", None)
        
        await update.message.reply_text(
            f"✅ <b>رسید شما دریافت شد</b>\n\n"
            f"🆔 شماره سفارش: <code>#{order.id}</code>\n"
            f"📦 پلن: {order.plan_name}\n"
            f"💰 مبلغ: {order.plan_price:,} تومان\n\n"
            f"⏳ سفارش شما در حال بررسی است\n"
            f"معمولاً کمتر از ۱ ساعت طول می‌کشد\n\n"
            f"🔔 پس از تایید، لینک اشتراک خودکار برایتان ارسال می‌شود.",
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML"
        )
        
        if not admin_ids:
            print("⚠️ No admin IDs configured!")
            return
        
        user_info = f"@{user.username}" if user.username else f"{user.first_name}"
        tg_user = db.query(TelegramUser).filter(TelegramUser.telegram_id == user.id).first()
        phone = tg_user.phone_number if tg_user and tg_user.phone_number else "ثبت نشده"
        
        admin_text = (
            f"🔔 <b>سفارش جدید</b>\n\n"
            f"🆔 شماره سفارش: <code>#{order.id}</code>\n"
            f"👤 کاربر: {user_info}\n"
            f"🆔 آیدی: <code>{user.id}</code>\n"
            f"📱 شماره: <code>{phone}</code>\n"
            f"📦 پلن: {order.plan_name}\n"
            f"💰 مبلغ: <b>{order.plan_price:,}</b> تومان\n"
            f"📅 زمان: {order.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
            f"👇 رسید در پیام بعدی"
        )
        
        for admin_id in admin_ids:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=admin_text,
                    parse_mode="HTML"
                )
                await context.bot.send_photo(
                    chat_id=admin_id,
                    photo=file_id,
                    caption=f"📸 رسید سفارش <code>#{order.id}</code>",
                    reply_markup=admin_order_keyboard(order.id),
                    parse_mode="HTML"
                )
            except Exception as e:
                print(f"Error sending to admin {admin_id}: {e}")
    finally:
        db.close()

async def cancel_order_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    order_id = int(query.data.replace("cancel_order_", ""))
    user = query.from_user
    db = get_db_session()
    
    try:
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.user_telegram_id == user.id
        ).first()
        
        if not order:
            await query.edit_message_text("❌ سفارش یافت نشد", reply_markup=back_to_menu())
            return
        
        if order.status == "approved":
            await query.edit_message_text(
                "❌ نمی‌توان سفارش تایید شده را لغو کرد",
                reply_markup=back_to_menu()
            )
            return
        
        order.status = "cancelled"
        db.commit()
        
        await query.edit_message_text(
            f"✅ سفارش <code>#{order.id}</code> لغو شد.\n\n"
            "می‌توانید دوباره از فروشگاه اقدام کنید.",
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML"
        )
    finally:
        db.close()