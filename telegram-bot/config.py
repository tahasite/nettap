import os
import time
import httpx
from dotenv import load_dotenv

load_dotenv()

BOT_DATABASE_URL = os.getenv("BOT_DATABASE_URL", "sqlite:////home/ubuntu/vpn-panel/data/bot.db")
NETTAP_API_URL = os.getenv("NETTAP_API_URL", "http://127.0.0.1:8734")
NETTAP_ADMIN_USER = os.getenv("NETTAP_ADMIN_USER", "admin")
NETTAP_ADMIN_PASS = os.getenv("NETTAP_ADMIN_PASS", "taha1234")

WEBHOOK_LISTEN_PORT = int(os.getenv("WEBHOOK_LISTEN_PORT", 8735))
USE_WEBHOOK = os.getenv("USE_WEBHOOK", "true").lower() == "true"

_settings_cache = {}
_settings_cache_time = 0
_plans_cache = None
_plans_cache_time = 0
CACHE_TTL = 60

_admin_token = None
_admin_token_time = 0

def get_admin_token_sync():
    global _admin_token, _admin_token_time
    now = time.time()
    if _admin_token and (now - _admin_token_time) < 300:
        return _admin_token
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                f"{NETTAP_API_URL}/api/auth/login",
                json={"username": NETTAP_ADMIN_USER, "password": NETTAP_ADMIN_PASS}
            )
            if response.status_code == 200:
                _admin_token = response.json().get("access_token")
                _admin_token_time = now
                return _admin_token
    except:
        pass
    return None

def reload_settings():
    global _settings_cache, _settings_cache_time
    token = get_admin_token_sync()
    if not token:
        return
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                f"{NETTAP_API_URL}/api/settings/",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                data = response.json()
                new_cache = {}
                for category in data:
                    for setting in category["settings"]:
                        new_cache[setting["key"]] = setting["value"]
                _settings_cache = new_cache
                _settings_cache_time = time.time()
    except Exception as e:
        print(f"Settings reload error: {e}")

def get_cached_settings():
    global _settings_cache_time
    now = time.time()
    if not _settings_cache or (now - _settings_cache_time) > CACHE_TTL:
        reload_settings()
    return _settings_cache

def setting(key: str, default: str = "") -> str:
    cache = get_cached_settings()
    return cache.get(key, default)

def setting_bool(key: str, default: bool = False) -> bool:
    val = setting(key, str(default).lower())
    return str(val).lower() in ["true", "1", "yes", "on"]

def setting_int(key: str, default: int = 0) -> int:
    try:
        return int(setting(key, str(default)))
    except:
        return default

def setting_list(key: str, separator: str = ",") -> list:
    val = setting(key, "")
    if not val:
        return []
    return [x.strip() for x in val.split(separator) if x.strip()]

def BOT_TOKEN():
    return setting("bot_token", "")

def ADMIN_IDS():
    val = setting("admin_ids", "")
    if not val:
        return []
    try:
        return [int(x.strip()) for x in val.split(",") if x.strip()]
    except:
        return []

def FORCE_JOIN_CHANNELS():
    return setting_list("force_join_channels")

def SUPPORT_USERNAME():
    return setting("support_username", "")

def CARD_NUMBER():
    return setting("payment_card_number", "")

def CARD_HOLDER():
    return setting("payment_card_holder", "")

def BRAND_NAME():
    return setting("brand_name", "NETtap")

def SUB_DOMAIN():
    return setting("sub_url_prefix", "https://vpn.tahasite.ir")

def TELEGRAM_API_PROXY():
    return setting("telegram_proxy", "")

def WEBHOOK_URL():
    return setting("webhook_url", "")

def BOT_ENABLED():
    return setting_bool("bot_enabled", True)

async def get_public_plans_async():
    import httpx
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{NETTAP_API_URL}/api/plans/public")
            if response.status_code == 200:
                return response.json()
    except:
        pass
    return None

async def get_active_plans():
    global _plans_cache, _plans_cache_time
    now = time.time()
    if _plans_cache is None or (now - _plans_cache_time) > CACHE_TTL:
        plans = await get_public_plans_async()
        if plans:
            _plans_cache = plans
            _plans_cache_time = now
    return _plans_cache or []

async def get_test_plan():
    plans = await get_active_plans()
    for p in plans:
        if p.get("is_test"):
            return p
    return None

async def get_shop_plans():
    plans = await get_active_plans()
    return [p for p in plans if not p.get("is_test")]

async def get_plan_by_key(plan_key):
    plans = await get_active_plans()
    for p in plans:
        if p["plan_key"] == plan_key:
            return p
    return None