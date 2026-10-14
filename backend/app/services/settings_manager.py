from sqlalchemy.orm import Session
from typing import Any, Optional
from app.models import Setting

_cache = {}
_cache_initialized = False

DEFAULT_SETTINGS = [
    {
        "key": "brand_name",
        "value": "NETtap",
        "category": "branding",
        "value_type": "text",
        "label_en": "Brand Name",
        "label_fa": "نام برند",
        "description_en": "Your service brand name displayed everywhere",
        "description_fa": "نام برند شما که در همه جا نمایش داده می‌شود",
        "is_public": True,
        "display_order": 1
    },
    {
        "key": "parent_brand",
        "value": "TahaSite",
        "category": "branding",
        "value_type": "text",
        "label_en": "Parent Company Name",
        "label_fa": "نام شرکت مادر",
        "description_en": "Parent company or organization name",
        "description_fa": "نام شرکت یا سازمان مادر",
        "is_public": True,
        "display_order": 2
    },
    {
        "key": "company_website",
        "value": "https://tahasite.ir",
        "category": "branding",
        "value_type": "url",
        "label_en": "Company Website",
        "label_fa": "وبسایت شرکت",
        "description_en": "Your main company website URL",
        "description_fa": "آدرس وبسایت اصلی شرکت شما",
        "is_public": True,
        "display_order": 3
    },
    {
        "key": "primary_color",
        "value": "#6366f1",
        "category": "branding",
        "value_type": "color",
        "label_en": "Primary Color",
        "label_fa": "رنگ اصلی",
        "description_en": "Main theme color used in panels and buttons",
        "description_fa": "رنگ اصلی تم که در پنل‌ها و دکمه‌ها استفاده می‌شود",
        "is_public": True,
        "display_order": 4
    },
    {
        "key": "secondary_color",
        "value": "#8b5cf6",
        "category": "branding",
        "value_type": "color",
        "label_en": "Secondary Color",
        "label_fa": "رنگ ثانویه",
        "description_en": "Secondary accent color",
        "description_fa": "رنگ تاکیدی ثانویه",
        "is_public": True,
        "display_order": 5
    },
    {
        "key": "panel_domain",
        "value": "vpn.tahasite.ir",
        "category": "domain",
        "value_type": "text",
        "label_en": "Panel Domain",
        "label_fa": "دامنه پنل",
        "description_en": "Admin panel and subscription domain",
        "description_fa": "دامنه پنل مدیریت و لینک اشتراک",
        "is_public": False,
        "display_order": 1
    },
    {
        "key": "sub_url_prefix",
        "value": "https://vpn.tahasite.ir",
        "category": "domain",
        "value_type": "url",
        "label_en": "Subscription URL Prefix",
        "label_fa": "پیشوند لینک اشتراک",
        "description_en": "Full URL prefix for subscription links",
        "description_fa": "پیشوند کامل آدرس برای لینک‌های اشتراک",
        "is_public": False,
        "display_order": 2
    },
    {
        "key": "dns_domain",
        "value": "nettap.ir",
        "category": "domain",
        "value_type": "text",
        "label_en": "DNS Domain",
        "label_fa": "دامنه DNS",
        "description_en": "Domain used for user subdomains",
        "description_fa": "دامنه مورد استفاده برای زیردامنه‌های کاربران",
        "is_public": False,
        "display_order": 3
    },
    {
        "key": "server_ip",
        "value": "95.38.163.161",
        "category": "domain",
        "value_type": "text",
        "label_en": "Server IP Address",
        "label_fa": "آی‌پی سرور",
        "description_en": "Public IP address of this server",
        "description_fa": "آی‌پی عمومی این سرور",
        "is_public": False,
        "display_order": 4
    },
    {
        "key": "bot_enabled",
        "value": "true",
        "category": "telegram",
        "value_type": "boolean",
        "label_en": "Enable Telegram Bot",
        "label_fa": "فعال‌سازی ربات تلگرام",
        "description_en": "Enable or disable the Telegram bot",
        "description_fa": "فعال یا غیرفعال کردن ربات تلگرام",
        "is_public": False,
        "display_order": 1
    },
    {
        "key": "bot_token",
        "value": "",
        "category": "telegram",
        "value_type": "password",
        "label_en": "Bot Token",
        "label_fa": "توکن ربات",
        "description_en": "Get it from @BotFather on Telegram",
        "description_fa": "از @BotFather در تلگرام دریافت کنید",
        "is_public": False,
        "is_secret": True,
        "display_order": 2
    },
    {
        "key": "bot_username",
        "value": "",
        "category": "telegram",
        "value_type": "text",
        "label_en": "Bot Username",
        "label_fa": "یوزرنیم ربات",
        "description_en": "Bot username without @ (e.g. mybot)",
        "description_fa": "یوزرنیم ربات بدون @ (مثل mybot)",
        "is_public": False,
        "display_order": 3
    },
    {
        "key": "admin_ids",
        "value": "",
        "category": "telegram",
        "value_type": "text",
        "label_en": "Admin Telegram IDs",
        "label_fa": "آیدی‌های تلگرام ادمین",
        "description_en": "Comma separated admin Telegram IDs (e.g. 123456789,987654321)",
        "description_fa": "آیدی‌های تلگرام ادمین با کاما جدا شود (مثل 123456789,987654321)",
        "is_public": False,
        "display_order": 4
    },
    {
        "key": "force_join_channels",
        "value": "",
        "category": "telegram",
        "value_type": "text",
        "label_en": "Force Join Channels",
        "label_fa": "کانال‌های عضویت اجباری",
        "description_en": "Comma separated channels with @ (e.g. @channel1,@channel2)",
        "description_fa": "کانال‌ها با @ و با کاما جدا شود (مثل @channel1,@channel2)",
        "is_public": False,
        "display_order": 5
    },
    {
        "key": "support_username",
        "value": "",
        "category": "telegram",
        "value_type": "text",
        "label_en": "Support Username",
        "label_fa": "یوزرنیم پشتیبانی",
        "description_en": "Support contact username with @ (e.g. @support)",
        "description_fa": "یوزرنیم پشتیبانی با @ (مثل @support)",
        "is_public": False,
        "display_order": 6
    },
    {
        "key": "telegram_proxy",
        "value": "",
        "category": "telegram",
        "value_type": "url",
        "label_en": "Telegram API Proxy",
        "label_fa": "پروکسی API تلگرام",
        "description_en": "Cloudflare Worker URL (for bypassing filters in Iran)",
        "description_fa": "آدرس Worker کلادفلر (برای دور زدن فیلتر در ایران)",
        "is_public": False,
        "display_order": 7
    },
    {
        "key": "webhook_url",
        "value": "",
        "category": "telegram",
        "value_type": "url",
        "label_en": "Webhook URL",
        "label_fa": "آدرس Webhook",
        "description_en": "Full webhook URL (e.g. https://domain.com/tgbot-webhook)",
        "description_fa": "آدرس کامل Webhook (مثل https://domain.com/tgbot-webhook)",
        "is_public": False,
        "display_order": 8
    },
    {
        "key": "payment_card_number",
        "value": "",
        "category": "payment",
        "value_type": "text",
        "label_en": "Card Number",
        "label_fa": "شماره کارت",
        "description_en": "Bank card number for payment (e.g. 6219-8618-xxxx-xxxx)",
        "description_fa": "شماره کارت بانکی برای پرداخت",
        "is_public": False,
        "display_order": 1
    },
    {
        "key": "payment_card_holder",
        "value": "",
        "category": "payment",
        "value_type": "text",
        "label_en": "Card Holder Name",
        "label_fa": "نام صاحب کارت",
        "description_en": "Full name of card holder",
        "description_fa": "نام کامل صاحب کارت",
        "is_public": False,
        "display_order": 2
    },
    {
        "key": "test_duration_minutes",
        "value": "15",
        "category": "subscription",
        "value_type": "number",
        "label_en": "Free Test Duration (minutes)",
        "label_fa": "مدت تست رایگان (دقیقه)",
        "description_en": "Duration of free test subscription in minutes",
        "description_fa": "مدت زمان اشتراک تست رایگان به دقیقه",
        "is_public": False,
        "display_order": 1
    },
    {
        "key": "default_language",
        "value": "en",
        "category": "general",
        "value_type": "select",
        "label_en": "Default Language",
        "label_fa": "زبان پیش‌فرض",
        "description_en": "Default language for subscription page",
        "description_fa": "زبان پیش‌فرض صفحه اشتراک",
        "is_public": True,
        "display_order": 1
    },
    {
        "key": "scraper_interval_hours",
        "value": "6",
        "category": "advanced",
        "value_type": "number",
        "label_en": "Scraper Interval (hours)",
        "label_fa": "فاصله بروزرسانی ساب‌ها (ساعت)",
        "description_en": "How often to fetch new configs from sellers",
        "description_fa": "هر چند ساعت یکبار از فروشندگان کانفیگ دریافت شود",
        "is_public": False,
        "display_order": 1
    },
    {
        "key": "dns_refresh_hours",
        "value": "1",
        "category": "advanced",
        "value_type": "number",
        "label_en": "DNS Refresh Interval (hours)",
        "label_fa": "فاصله بروزرسانی DNS (ساعت)",
        "description_en": "How often to refresh DNS mappings",
        "description_fa": "هر چند ساعت DNS ها بروزرسانی شوند",
        "is_public": False,
        "display_order": 2
    },
    {
        "key": "cleanup_days",
        "value": "7",
        "category": "advanced",
        "value_type": "number",
        "label_en": "Cleanup Unused Days",
        "label_fa": "روزهای پاک‌سازی موارد بلااستفاده",
        "description_en": "Days before unused DNS mappings are deleted",
        "description_fa": "پس از چند روز موارد بلااستفاده پاک شوند",
        "is_public": False,
        "display_order": 3
    },
]

CATEGORIES_META = {
    "general": {"label_en": "General", "label_fa": "عمومی", "icon": "fa-cog", "order": 1},
    "branding": {"label_en": "Branding", "label_fa": "برندینگ", "icon": "fa-palette", "order": 2},
    "domain": {"label_en": "Domain & DNS", "label_fa": "دامنه و DNS", "icon": "fa-globe", "order": 3},
    "telegram": {"label_en": "Telegram Bot", "label_fa": "ربات تلگرام", "icon": "fa-robot", "order": 4},
    "payment": {"label_en": "Payment", "label_fa": "پرداخت", "icon": "fa-credit-card", "order": 5},
    "subscription": {"label_en": "Subscription", "label_fa": "اشتراک", "icon": "fa-ticket", "order": 6},
    "advanced": {"label_en": "Advanced", "label_fa": "پیشرفته", "icon": "fa-gears", "order": 7},
}

def seed_default_settings(db: Session):
    for item in DEFAULT_SETTINGS:
        existing = db.query(Setting).filter(Setting.key == item["key"]).first()
        if not existing:
            setting = Setting(**item)
            db.add(setting)
    db.commit()
    reload_cache(db)

def reload_cache(db: Session):
    global _cache, _cache_initialized
    _cache = {}
    settings = db.query(Setting).all()
    for s in settings:
        _cache[s.key] = s.value
    _cache_initialized = True

def get_setting(db: Session, key: str, default: Any = None) -> Any:
    global _cache_initialized
    if not _cache_initialized:
        reload_cache(db)
    return _cache.get(key, default)

def get_setting_bool(db: Session, key: str, default: bool = False) -> bool:
    value = get_setting(db, key, str(default).lower())
    return str(value).lower() in ["true", "1", "yes", "on"]

def get_setting_int(db: Session, key: str, default: int = 0) -> int:
    try:
        return int(get_setting(db, key, default))
    except:
        return default

def get_setting_list(db: Session, key: str, separator: str = ",") -> list:
    value = get_setting(db, key, "")
    if not value:
        return []
    return [x.strip() for x in value.split(separator) if x.strip()]

def set_setting(db: Session, key: str, value: str):
    from datetime import datetime
    setting = db.query(Setting).filter(Setting.key == key).first()
    if setting:
        setting.value = str(value)
        setting.updated_at = datetime.utcnow()
        db.commit()
        _cache[key] = str(value)
    return setting

def get_all_grouped(db: Session) -> list:
    settings = db.query(Setting).order_by(Setting.category, Setting.display_order).all()
    grouped = {}
    for s in settings:
        if s.category not in grouped:
            grouped[s.category] = []
        grouped[s.category].append(s)
    
    result = []
    for cat_key, meta in sorted(CATEGORIES_META.items(), key=lambda x: x[1]["order"]):
        if cat_key in grouped:
            result.append({
                "category": cat_key,
                "label_en": meta["label_en"],
                "label_fa": meta["label_fa"],
                "icon": meta["icon"],
                "settings": grouped[cat_key]
            })
    return result