from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from config import SUPPORT_USERNAME

def main_menu_keyboard():
    support = SUPPORT_USERNAME()
    support_url = f"https://t.me/{support.replace('@','')}" if support else "https://t.me/"
    
    keyboard = [
        [
            InlineKeyboardButton("🎁 دریافت تست رایگان", callback_data="get_test"),
            InlineKeyboardButton("🛒 خرید اشتراک", callback_data="shop")
        ],
        [
            InlineKeyboardButton("📊 اشتراک‌های من", callback_data="my_subs")
        ],
        [
            InlineKeyboardButton("📚 آموزش اتصال", callback_data="tutorial"),
            InlineKeyboardButton("💬 پشتیبانی", url=support_url)
        ],
        [
            InlineKeyboardButton("🔗 معرفی به دوستان", callback_data="referral")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def shop_keyboard(plans: list):
    buttons = []
    for plan in plans:
        price_text = f"{plan['price']:,} تومان" if plan['price'] > 0 else "رایگان"
        buttons.append([
            InlineKeyboardButton(
                text=f"{plan['emoji']} {plan['name']} — {price_text}",
                callback_data=f"buy_{plan['plan_key']}"
            )
        ])
    buttons.append([InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")])
    return InlineKeyboardMarkup(buttons)

def payment_keyboard(order_id: int):
    keyboard = [
        [InlineKeyboardButton("📤 ارسال رسید پرداخت", callback_data=f"send_receipt_{order_id}")],
        [InlineKeyboardButton("❌ لغو سفارش", callback_data=f"cancel_order_{order_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)

def tutorial_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("📱 اندروید (V2rayNG)", callback_data="tut_android"),
            InlineKeyboardButton("🍎 آی‌اواس (V2Box)", callback_data="tut_ios")
        ],
        [
            InlineKeyboardButton("💻 ویندوز (v2rayN)", callback_data="tut_windows"),
            InlineKeyboardButton("🖥 مک (V2Box)", callback_data="tut_mac")
        ],
        [
            InlineKeyboardButton("⭐ Hiddify (پیشنهادی)", callback_data="tut_hiddify")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def admin_order_keyboard(order_id: int):
    keyboard = [
        [
            InlineKeyboardButton("✅ تایید و ساخت اکانت", callback_data=f"approve_{order_id}"),
            InlineKeyboardButton("❌ رد سفارش", callback_data=f"reject_{order_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def back_to_menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]])

def phone_request_keyboard():
    keyboard = [[KeyboardButton("📱 ارسال شماره تلفن", request_contact=True)]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)