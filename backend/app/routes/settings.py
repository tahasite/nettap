from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from app.database import get_db
from app.models import Setting
from app.schemas import SettingResponse, SettingUpdate, SettingBulkUpdate
from app.utils.deps import get_current_admin
from app.services.settings_manager import (
    get_all_grouped, set_setting, reload_cache, CATEGORIES_META, get_setting
)
from app.services.bot_manager import (
    test_bot_token, test_proxy, check_bot_in_channel,
    set_webhook, delete_webhook, get_webhook_info,
    restart_bot_service, get_bot_service_status, full_setup_bot
)

router = APIRouter(prefix="/api/settings", tags=["settings"])

class TestTokenRequest(BaseModel):
    token: str = None

class TestProxyRequest(BaseModel):
    proxy_url: str = None

class TestChannelRequest(BaseModel):
    channel: str

@router.get("/")
def get_all_settings(
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    grouped = get_all_grouped(db)
    result = []
    for group in grouped:
        settings_list = []
        for s in group["settings"]:
            settings_list.append({
                "id": s.id,
                "key": s.key,
                "value": s.value,
                "category": s.category,
                "value_type": s.value_type,
                "label_en": s.label_en,
                "label_fa": s.label_fa,
                "description_en": s.description_en,
                "description_fa": s.description_fa,
                "is_public": s.is_public,
                "is_secret": s.is_secret,
                "display_order": s.display_order,
                "updated_at": s.updated_at
            })
        result.append({
            "category": group["category"],
            "label_en": group["label_en"],
            "label_fa": group["label_fa"],
            "icon": group["icon"],
            "settings": settings_list
        })
    return result

@router.get("/public")
def get_public_settings(db: Session = Depends(get_db)):
    settings = db.query(Setting).filter(Setting.is_public == True).all()
    result = {}
    for s in settings:
        result[s.key] = s.value
    return result

@router.get("/{key}", response_model=SettingResponse)
def get_single_setting(
    key: str,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    setting = db.query(Setting).filter(Setting.key == key).first()
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    return setting

@router.patch("/{key}")
def update_setting(
    key: str,
    data: SettingUpdate,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    setting = db.query(Setting).filter(Setting.key == key).first()
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    
    set_setting(db, key, data.value)
    return {"status": "success", "key": key, "value": data.value}

@router.post("/bulk-update")
def bulk_update_settings(
    data: SettingBulkUpdate,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    updated = []
    failed = []
    telegram_changed = False
    telegram_keys = ["bot_token", "bot_username", "telegram_proxy", "webhook_url", "bot_enabled"]
    
    for key, value in data.settings.items():
        setting = db.query(Setting).filter(Setting.key == key).first()
        if setting:
            set_setting(db, key, str(value))
            updated.append(key)
            if key in telegram_keys:
                telegram_changed = True
        else:
            failed.append(key)
    
    return {
        "status": "success",
        "updated_count": len(updated),
        "failed_count": len(failed),
        "updated": updated,
        "failed": failed,
        "telegram_changed": telegram_changed
    }

@router.post("/reload-cache")
def reload_settings_cache(
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    reload_cache(db)
    return {"status": "success", "message": "Settings cache reloaded"}

@router.get("/categories/list")
def get_categories(
    current_admin: str = Depends(get_current_admin)
):
    result = []
    for cat_key, meta in sorted(CATEGORIES_META.items(), key=lambda x: x[1]["order"]):
        result.append({
            "key": cat_key,
            "label_en": meta["label_en"],
            "label_fa": meta["label_fa"],
            "icon": meta["icon"],
            "order": meta["order"]
        })
    return result

@router.post("/telegram/test-token")
async def test_telegram_token(
    data: TestTokenRequest,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    result = await test_bot_token(db, data.token)
    return result

@router.post("/telegram/test-proxy")
async def test_telegram_proxy(
    data: TestProxyRequest,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    result = await test_proxy(db, data.proxy_url)
    return result

@router.post("/telegram/test-channel")
async def test_telegram_channel(
    data: TestChannelRequest,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    result = await check_bot_in_channel(db, data.channel)
    return result

@router.get("/telegram/webhook-info")
async def get_telegram_webhook_info(
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    result = await get_webhook_info(db)
    return result

@router.post("/telegram/set-webhook")
async def set_telegram_webhook(
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    result = await set_webhook(db)
    return result

@router.post("/telegram/delete-webhook")
async def delete_telegram_webhook(
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    result = await delete_webhook(db)
    return result

@router.get("/telegram/service-status")
def get_telegram_service_status(
    current_admin: str = Depends(get_current_admin)
):
    return get_bot_service_status()

@router.post("/telegram/restart-service")
def restart_telegram_service(
    current_admin: str = Depends(get_current_admin)
):
    return restart_bot_service()

@router.post("/telegram/full-setup")
async def full_telegram_setup(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    result = await full_setup_bot(db)
    
    if result.get("needs_restart"):
        background_tasks.add_task(restart_bot_service)
    
    return result