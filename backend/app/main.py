import os
import uvicorn
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from app.database import Base, engine, SessionLocal
from app.models import Admin, UserSubscription
from app.utils.security import get_password_hash
from app.routes import auth, sellers, users, sub, configs, groups, jobs, plans, settings
from app.services.scraper import run_scraper
from app.services.dns_manager import refresh_all_ips, cleanup_stale_mappings, rebuild_zone_file
from app.services.job_logger import log_job
from app.services.settings_manager import seed_default_settings, get_setting_int

load_dotenv()

Base.metadata.create_all(bind=engine)

def seed_admin():
    db = SessionLocal()
    try:
        admin_exists = db.query(Admin).first()
        if not admin_exists:
            hashed_pw = get_password_hash("taha1234")
            default_admin = Admin(username="admin", password_hash=hashed_pw)
            db.add(default_admin)
            db.commit()
    finally:
        db.close()

def seed_settings():
    db = SessionLocal()
    try:
        seed_default_settings(db)
    finally:
        db.close()

seed_admin()
seed_settings()

def job_scraper():
    def task(db):
        run_scraper(db)
        return "Sellers scraped"
    log_job("scraper", task)

def job_dns_refresh():
    def task(db):
        count = refresh_all_ips(db)
        return f"Updated {count} IPs"
    log_job("dns_refresh", task)

def job_cleanup_stale():
    def task(db):
        cleanup_days = get_setting_int(db, "cleanup_days", 7)
        count = cleanup_stale_mappings(db, days_unused=cleanup_days)
        return f"Cleaned {count} stale mappings"
    log_job("cleanup_stale", task)

def job_check_expired():
    def task(db):
        now = datetime.utcnow()
        expired_users = db.query(UserSubscription).filter(
            UserSubscription.expire_date != None,
            UserSubscription.expire_date < now,
            UserSubscription.is_active == True
        ).all()
        
        count = 0
        for user in expired_users:
            user.is_active = False
            count += 1
        db.commit()
        
        if count > 0:
            rebuild_zone_file(db)
        
        return f"Expired {count} users, DNS updated"
    log_job("check_expired", task)

def job_rebuild_zone():
    def task(db):
        rebuild_zone_file(db)
        return "Zone file rebuilt"
    log_job("rebuild_zone", task)

def get_schedule_hours(key: str, default: int) -> int:
    db = SessionLocal()
    try:
        return get_setting_int(db, key, default)
    finally:
        db.close()

scheduler = BackgroundScheduler()
scheduler.add_job(job_scraper, 'interval', hours=get_schedule_hours("scraper_interval_hours", 6), id='scraper')
scheduler.add_job(job_dns_refresh, 'interval', hours=get_schedule_hours("dns_refresh_hours", 1), id='dns_refresh')
scheduler.add_job(job_cleanup_stale, 'interval', hours=12, id='cleanup_stale')
scheduler.add_job(job_check_expired, 'interval', minutes=1, id='check_expired')
scheduler.add_job(job_rebuild_zone, 'interval', minutes=5, id='rebuild_zone')
scheduler.start()

app = FastAPI(title=os.getenv("PROJECT_NAME", "NETtap API"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(sellers.router)
app.include_router(users.router)
app.include_router(sub.router)
app.include_router(configs.router)
app.include_router(groups.router)
app.include_router(jobs.router)
app.include_router(plans.router)
app.include_router(settings.router)

@app.get("/")
def read_root():
    db = SessionLocal()
    try:
        from app.services.settings_manager import get_setting
        brand = get_setting(db, "brand_name", "NETtap")
        return {"status": "running", "service": f"{brand} API", "version": "1.0.0"}
    finally:
        db.close()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", 8734)),
        reload=True
    )