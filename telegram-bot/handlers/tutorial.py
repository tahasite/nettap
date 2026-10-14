from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from keyboards import tutorial_keyboard, back_to_menu

TUTORIALS = {
    "android": {
        "title": "📱 آموزش اندروید (V2rayNG)",
        "app_link": "https://play.google.com/store/apps/details?id=com.v2ray.ang",
        "steps": [
            "1️⃣ برنامه V2rayNG را از پلی استور یا لینک زیر دانلود کنید",
            "2️⃣ لینک اشتراک خود را کپی کنید (از بخش «اشتراک‌های من»)",
            "3️⃣ در برنامه، روی آیکون <b>+</b> بالای صفحه بزنید",
            "4️⃣ گزینه <b>«Import config from Clipboard»</b> را انتخاب کنید",
            "5️⃣ یا از گزینه <b>«Add subscription»</b> و آدرس ساب را وارد کنید",
            "6️⃣ روی <b>«Update subscription»</b> بزنید",
            "7️⃣ یکی از سرورها را انتخاب و روی دکمه اتصال بزنید ✅"
        ]
    },
    "ios": {
        "title": "🍎 آموزش آیفون (V2Box)",
        "app_link": "https://apps.apple.com/us/app/v2box-v2ray-client/id6446814690",
        "steps": [
            "1️⃣ برنامه V2Box را از اپ استور نصب کنید",
            "2️⃣ لینک اشتراک خود را کپی کنید",
            "3️⃣ در برنامه، به تب <b>Configs</b> بروید",
            "4️⃣ روی <b>+</b> بزنید و <b>«Import v2ray uri from clipboard»</b> را انتخاب کنید",
            "5️⃣ یا <b>«Add subscribe»</b> و لینک را وارد کنید",
            "6️⃣ به تب <b>Home</b> برگردید",
            "7️⃣ یک سرور انتخاب کنید و دکمه اتصال را بزنید ✅"
        ]
    },
    "windows": {
        "title": "💻 آموزش ویندوز (v2rayN)",
        "app_link": "https://github.com/2dust/v2rayN/releases/latest",
        "steps": [
            "1️⃣ برنامه v2rayN را از گیت‌هاب دانلود و اجرا کنید",
            "2️⃣ لینک اشتراک خود را کپی کنید",
            "3️⃣ در بالای برنامه، منوی <b>Subscription</b> را باز کنید",
            "4️⃣ گزینه <b>Subscription setting</b> را بزنید",
            "5️⃣ در جدول، ردیف جدید اضافه کنید و آدرس ساب را در ستون URL بگذارید",
            "6️⃣ روی <b>Update subscriptions</b> بزنید",
            "7️⃣ یک سرور انتخاب کرده و از منوی <b>System proxy</b> گزینه <b>Set system proxy</b> را بزنید ✅"
        ]
    },
    "mac": {
        "title": "🖥 آموزش مک (V2Box)",
        "app_link": "https://apps.apple.com/us/app/v2box-v2ray-client/id6446814690",
        "steps": [
            "1️⃣ برنامه V2Box را از Mac App Store نصب کنید",
            "2️⃣ لینک اشتراک خود را کپی کنید",
            "3️⃣ در برنامه، به تب <b>Configs</b> بروید",
            "4️⃣ روی <b>+</b> بزنید و آدرس ساب را وارد کنید",
            "5️⃣ صبر کنید تا سرورها لود شوند",
            "6️⃣ یک سرور انتخاب کنید و دکمه اتصال را بزنید ✅"
        ]
    },
    "hiddify": {
        "title": "⭐ آموزش Hiddify (پیشنهادی)",
        "app_link": "https://hiddify.com/app/",
        "steps": [
            "🌟 <b>چرا Hiddify پیشنهاد ما است؟</b>\n"
            "├ سریع‌ترین کلاینت VPN\n"
            "├ رابط کاربری زیبا\n"
            "├ پشتیبانی از همه پلتفرم‌ها\n"
            "└ اتصال هوشمند به بهترین سرور\n",
            "1️⃣ برنامه Hiddify را از سایت رسمی دانلود کنید",
            "2️⃣ لینک اشتراک خود را کپی کنید",
            "3️⃣ برنامه را باز کنید",
            "4️⃣ روی دکمه <b>«افزودن پروکسی»</b> بزنید",
            "5️⃣ گزینه <b>«افزودن از کلیپ‌بورد»</b> را انتخاب کنید",
            "6️⃣ برنامه خودکار سرورها را لود می‌کند",
            "7️⃣ روی دکمه بزرگ اتصال بزنید ✅"
        ]
    }
}

async def tutorial_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = (
        "📚 <b>آموزش اتصال به NETtap</b>\n\n"
        "دستگاه خود را انتخاب کنید:\n\n"
        "💡 <b>پیشنهاد ما:</b> Hiddify\n"
        "(سریع‌ترین و راحت‌ترین کلاینت)"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=tutorial_keyboard(),
        parse_mode="HTML"
    )

async def tutorial_platform_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    platform = query.data.replace("tut_", "")
    tutorial = TUTORIALS.get(platform)
    
    if not tutorial:
        await query.edit_message_text("❌ آموزش یافت نشد", reply_markup=back_to_menu())
        return
    
    text = f"<b>{tutorial['title']}</b>\n\n"
    text += "\n\n".join(tutorial["steps"])
    text += f"\n\n🔗 <b>لینک دانلود:</b>\n{tutorial['app_link']}"
    
    keyboard = [
        [InlineKeyboardButton("📥 دانلود برنامه", url=tutorial["app_link"])],
        [InlineKeyboardButton("🔙 بازگشت به آموزش‌ها", callback_data="tutorial")],
        [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
        disable_web_page_preview=True
    )