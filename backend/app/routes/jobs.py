from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import CronJobLog
from app.schemas import CronJobLogResponse
from app.utils.deps import get_current_admin

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

@router.get("/logs", response_model=List[CronJobLogResponse])
def get_job_logs(
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    logs = db.query(CronJobLog).order_by(CronJobLog.executed_at.desc()).limit(100).all()
    return logs

@router.get("/summary")
def get_jobs_summary(
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    from sqlalchemy import func
    
    latest = db.query(
        CronJobLog.job_name,
        func.max(CronJobLog.executed_at).label('last_run')
    ).group_by(CronJobLog.job_name).all()
    
    result = []
    for job_name, last_run in latest:
        log = db.query(CronJobLog).filter(
            CronJobLog.job_name == job_name,
            CronJobLog.executed_at == last_run
        ).first()
        if log:
            result.append({
                "job_name": job_name,
                "last_run": log.executed_at,
                "status": log.status,
                "message": log.message,
                "duration_ms": log.duration_ms
            })
    return result