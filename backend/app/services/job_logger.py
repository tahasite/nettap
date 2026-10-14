import time
from datetime import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import CronJobLog

def log_job(job_name: str, func):
    db = SessionLocal()
    start = time.time()
    status = "success"
    message = ""
    result = None
    
    try:
        result = func(db)
        if isinstance(result, dict):
            message = str(result)
        elif result is not None:
            message = str(result)
    except Exception as e:
        status = "error"
        message = str(e)[:500]
    
    duration_ms = int((time.time() - start) * 1000)
    
    try:
        log = CronJobLog(
            job_name=job_name,
            status=status,
            message=message[:500] if message else "",
            duration_ms=duration_ms,
            executed_at=datetime.utcnow()
        )
        db.add(log)
        db.commit()
        
        old_logs = db.query(CronJobLog).filter(CronJobLog.job_name == job_name).order_by(CronJobLog.executed_at.desc()).offset(50).all()
        for old in old_logs:
            db.delete(old)
        db.commit()
    except:
        pass
    finally:
        db.close()
    
    return result