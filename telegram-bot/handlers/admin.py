from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from database import get_db_session, TelegramUser, Order, BotSubscription
from config import ADMIN_IDS, BRAND_NAME, get_plan_by_key
from services.nettap_api import create_user
from keyboards import main_menu_keyboard

async def admin_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admin_ids = ADMIN_IDS()
    
    if user_id not in admin_ids:
        return
        
    db = get_db_session()
    brand = BRAND_NAME()
    
    try:
        total_users = db.query(TelegramUser).count()
        pending_orders = db.query(Order).filter(Order.status == "pending").count()
        active_subs = db.query(BotSubscription).count()
        
        text = (
            f"👨‍💼 <b>پنل مدیریت ربات {brand}</b>\n\n"
            f"👥 کل کاربران ربات: {total_users} نفر\n"
            f"⏳ سفارشات منتظر تایید: {pending_orders} مورد\n"
            f"📡 اشتراک‌های فعال: {active_subs} مورد\n\n"
            f"📥 <b>دستورات مدیریت:</b>\n"
            f"├ ارسال پیام همگانی:\n"
            f"<code>/broadcast متن پیام</code>\n"
            f"├ بارگذاری مجدد تنظیمات:\n"
            f"<code>/reload</code>\n"
        )
        await update.message.reply_text(text, parse_mode="HTML")
    finally:
        db.close()

async def approve_order_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    admin_id = query.from_user.id
    admin_ids = ADMIN_IDS()
    
    if admin_id not in admin_ids:
        await query.answer("❌ دسترسی غیرمجاز", show_alert=True)
        return
        
    order_id = int(query.data.replace("approve_", ""))
    db = get_db_session()
    
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            await query.answer("❌ سفارش یافت نشد", show_alert=True)
            return
            
        if order.status == "approved":
            await query.answer("⚠️ این سفارش قبلاً تایید شده است", show_alert=True)
            return
            
        await query.edit_message_caption("⏳ در حال ساخت اکانت و ارسال...")
        
        plan = await get_plan_by_key(order.plan_id)
        group_id = plan.get("group_id") if plan else None
        
        username = f"user_{order.user_telegram_id}_{order.id}"
        result = await create_user(
            username=username, 
            duration_minutes=order.plan_minutes,
            group_id=group_id
        )
        
        if not result:
            await query.edit_message_caption("❌ خطا در ساخت کانفیگ در پنل اصلی")
            return
            
        sub_url = result["sub_url"]
        sub_token = result["token"]
        
        order.status = "approved"
        order.approved_at = datetime.utcnow()
        order.approved_by = admin_id
        order.sub_username = username
        order.sub_token = sub_token
        order.sub_url = sub_url
        
        user = db.query(TelegramUser).filter(TelegramUser.telegram_id == order.user_telegram_id).first()
        if user and user.referred_by:
            referrer = db.query(TelegramUser).filter(TelegramUser.telegram_id == user.referred_by).first()
            if referrer:
                bonus = int(order.plan_price * 0.20)
                referrer.balance += bonus
                try:
                    await context.bot.send_message(
                        chat_id=referrer.telegram_id,
                        text=(
                            f"🎁 <b>اعتبار هدیه دریافت شد!</b>\n\n"
                            f"کاربر معرفی شده توسط شما خریدی انجام داد و مبلغ <b>{bonus:,} تومان</b> اعتبار به کیف پول شما اضافه شد. 🎉"
                        ),
                        parse_mode="HTML"
                    )
                except:
                    pass
                    
        bot_sub = BotSubscription(
            user_telegram_id=order.user_telegram_id,
            sub_username=username,
            sub_token=sub_token,
            sub_url=sub_url,
            plan_id=order.plan_id,
            duration_minutes=order.plan_minutes,
            is_test=False,
            order_id=order.id,
            created_at=datetime.utcnow()
        )
        db.add(bot_sub)
        db.commit()
        
        await query.edit_message_caption(f"✅ سفارش <code>#{order.id}</code> با موفقیت تایید و ارسال شد.", parse_mode="HTML")
        
        duration_text = ""
        if order.plan_minutes >= 1440:
            duration_text = f"{order.plan_minutes // 1440} روز"
        elif order.plan_minutes >= 60:
            duration_text = f"{order.plan_minutes // 60} ساعت"
        else:
            duration_text = f"{order.plan_minutes} دقیقه"
        
        user_msg = (
            f"🎉 <b>سفارش شما تایید شد!</b>\n\n"
            f"📦 <b>پلن:</b> {order.plan_name}\n"
            f"⏱ <b>مدت:</b> {duration_text}\n"
            f"♾ <b>حجم:</b> نامحدود\n\n"
            f"🔗 <b>لینک اشتراک اختصاصی شما:</b>\n"
            f"<code>{sub_url}</code>\n\n"
            f"💡 برای آموزش نحوه اضافه کردن لینک به برنامه، دکمه «📚 آموزش اتصال» را لمس کنید."
        )
        
        await context.bot.send_message(
            chat_id=order.user_telegram_id,
            text=user_msg,
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML"
        )
        
    except Exception as e:
        await query.edit_message_caption(f"❌ خطا: {str(e)}")
    finally:
        db.close()

async def reject_order_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    admin_id = query.from_user.id
    admin_ids = ADMIN_IDS()
    
    if admin_id not in admin_ids:
        return
        
    order_id = int(query.data.replace("reject_", ""))
    context.user_data["waiting_reject_reason_for"] = order_id
    
    await query.edit_message_caption(
        f"❌ <b>رد سفارش #{order_id}</b>\n\n"
        f"لطفاً علت رد سفارش را بنویسید و روی این پیام ریپلای کنید. (مثال: واریز نامعتبر)"
    )

async def admin_reject_reason_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = update.effective_user.id
    admin_ids = ADMIN_IDS()
    
    if admin_id not in admin_ids:
        return
        
    order_id = context.user_data.get("waiting_reject_reason_for")
    if not order_id:
        return
        
    reason = update.message.text
    db = get_db_session()
    
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            await update.message.reply_text("❌ سفارش یافت نشد")
            return
            
        order.status = "rejected"
        order.admin_note = reason
        db.commit()
        
        context.user_data.pop("waiting_reject_reason_for", None)
        
        await update.message.reply_text(f"✅ سفارش <code>#{order_id}</code> با موفقیت رد شد و به کاربر اطلاع داده شد.", parse_mode="HTML")
        
        user_msg = (
            f"❌ <b>سفارش شما رد شد</b>\n\n"
            f"🆔 شماره سفارش: <code>#{order_id}</code>\n"
            f"📦 پلن: {order.plan_name}\n\n"
            f"📝 <b>علت رد سفارش:</b>\n"
            f"« {reason} »\n\n"
            f"در صورت بروز هرگونه ابهام، به پشتیبانی پیام بدهید."
        )
        
        await context.bot.send_message(
            chat_id=order.user_telegram_id,
            text=user_msg,
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML"
        )
    finally:
        db.close()

async def broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = update.effective_user.id
    admin_ids = ADMIN_IDS()
    
    if admin_id not in admin_ids:
        return
        
    if not context.args:
        await update.message.reply_text("❌ دستور اشتباه. مثال:\n<code>/broadcast سلام همگی</code>", parse_mode="HTML")
        return
        
    text = " ".join(context.args)
    db = get_db_session()
    
    try:
        users = db.query(TelegramUser).filter(TelegramUser.is_banned == False).all()
        await update.message.reply_text(f"⏳ ارسال پیام همگانی برای {len(users)} کاربر آغاز شد...")
        
        success = 0
        failed = 0
        
        for user in users:
            try:
                await context.bot.send_message(
                    chat_id=user.telegram_id,
                    text=text,
                    parse_mode="HTML"
                )
                success += 1
            except:
                failed += 1
                
        await update.message.reply_text(
            f"✅ <b>ارسال کامل شد</b>\n\n"
            f"├ موفق: {success}\n"
            f"└ ناموفق: {failed}",
            parse_mode="HTML"
        )
    finally:
        db.close()