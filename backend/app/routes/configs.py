from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime
from pydantic import BaseModel
from app.database import get_db, SessionLocal
from app.models import ExtractedConfig, SellerSubscription
from app.utils.deps import get_current_admin
from app.services.geo_ping import scan_all_configs, detect_country_for_config, ping_config

router = APIRouter(prefix="/api/configs", tags=["configs"])

class ConfigResponse(BaseModel):
    id: int
    seller_sub_id: int
    seller_name: str
    name: str
    protocol: str
    country_code: str
    country_flag: str
    ping: int
    is_working: bool
    is_pinned: bool
    last_checked: datetime
    raw_config: str

    class Config:
        from_attributes = True

class ConfigStats(BaseModel):
    total: int
    working: int
    broken: int
    pinned: int
    by_protocol: dict
    by_country: dict

@router.get("/stats", response_model=ConfigStats)
def get_configs_stats(
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    total = db.query(ExtractedConfig).count()
    working = db.query(ExtractedConfig).filter(ExtractedConfig.is_working == True).count()
    broken = total - working
    pinned = db.query(ExtractedConfig).filter(ExtractedConfig.is_pinned == True).count()
    
    protocol_stats = db.query(
        ExtractedConfig.protocol,
        func.count(ExtractedConfig.id)
    ).group_by(ExtractedConfig.protocol).all()
    
    by_protocol = {p: c for p, c in protocol_stats}
    
    country_stats = db.query(
        ExtractedConfig.country_flag,
        func.count(ExtractedConfig.id)
    ).group_by(ExtractedConfig.country_flag).all()
    
    by_country = {c: cnt for c, cnt in country_stats}
    
    return ConfigStats(
        total=total,
        working=working,
        broken=broken,
        pinned=pinned,
        by_protocol=by_protocol,
        by_country=by_country
    )

@router.get("/", response_model=List[ConfigResponse])
def get_configs(
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    configs = db.query(ExtractedConfig).all()
    result = []
    for c in configs:
        seller = db.query(SellerSubscription).filter(SellerSubscription.id == c.seller_sub_id).first()
        result.append(ConfigResponse(
            id=c.id,
            seller_sub_id=c.seller_sub_id,
            seller_name=seller.name if seller else "Unknown",
            name=c.name,
            protocol=c.protocol,
            country_code=c.country_code or "XX",
            country_flag=c.country_flag or "🌍",
            ping=c.ping,
            is_working=c.is_working,
            is_pinned=c.is_pinned,
            last_checked=c.last_checked,
            raw_config=c.raw_config
        ))
    return result

@router.post("/{config_id}/pin")
def toggle_pin(
    config_id: int,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    config = db.query(ExtractedConfig).filter(ExtractedConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    config.is_pinned = not config.is_pinned
    db.commit()
    return {"message": "Toggled", "is_pinned": config.is_pinned}

@router.post("/pin-all")
def pin_all(
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    db.query(ExtractedConfig).update({"is_pinned": True})
    db.commit()
    count = db.query(ExtractedConfig).count()
    return {"message": "All pinned", "count": count}

@router.post("/unpin-all")
def unpin_all(
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    db.query(ExtractedConfig).update({"is_pinned": False})
    db.commit()
    return {"message": "All unpinned"}

@router.post("/delete-broken")
def delete_broken(
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    deleted = db.query(ExtractedConfig).filter(ExtractedConfig.is_working == False).delete()
    db.commit()
    return {"message": "Broken configs deleted", "count": deleted}

def background_scan(do_country: bool, do_ping: bool):
    db = SessionLocal()
    try:
        scan_all_configs(db, do_country=do_country, do_ping=do_ping)
    finally:
        db.close()

@router.post("/scan-countries")
def scan_countries(
    background_tasks: BackgroundTasks,
    current_admin: str = Depends(get_current_admin)
):
    background_tasks.add_task(background_scan, True, False)
    return {"message": "Country detection started in background"}

@router.post("/scan-ping")
def scan_ping(
    background_tasks: BackgroundTasks,
    current_admin: str = Depends(get_current_admin)
):
    background_tasks.add_task(background_scan, False, True)
    return {"message": "Ping test started in background"}

@router.post("/scan-all")
def scan_all(
    background_tasks: BackgroundTasks,
    current_admin: str = Depends(get_current_admin)
):
    background_tasks.add_task(background_scan, True, True)
    return {"message": "Full scan (country + ping) started in background"}

@router.post("/{config_id}/test")
def test_single_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    config = db.query(ExtractedConfig).filter(ExtractedConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    
    ping = ping_config(config)
    code, flag = detect_country_for_config(config)
    
    config.ping = ping
    config.country_code = code
    config.country_flag = flag
    config.is_working = ping > 0
    config.last_checked = datetime.utcnow()
    db.commit()
    
    return {
        "ping": ping,
        "country_code": code,
        "country_flag": flag,
        "is_working": ping > 0
    }

@router.delete("/{config_id}")
def delete_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    config = db.query(ExtractedConfig).filter(ExtractedConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    db.delete(config)
    db.commit()
    return {"message": "Config deleted successfully"}