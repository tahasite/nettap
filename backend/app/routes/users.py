import base64
import secrets
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import UserSubscription
from app.schemas import UserSubscriptionCreate, UserSubscriptionResponse, UserSubscriptionUpdate
from app.utils.deps import get_current_admin
from app.services.dns_manager import block_user_mappings, unblock_user_mappings, delete_user_mappings

router = APIRouter(prefix="/api/users", tags=["users"])

def generate_secure_token(user_id: int = None) -> str:
    timestamp = int(datetime.utcnow().timestamp())
    user_part = user_id if user_id else secrets.randbelow(99999)
    data_str = f"v3,{user_part},{timestamp}"
    data_b64 = base64.urlsafe_b64encode(data_str.encode()).decode().rstrip('=')
    signature_bytes = secrets.token_bytes(32)
    signature_b64 = base64.urlsafe_b64encode(signature_bytes).decode().rstrip('=')
    return f"{data_b64}.{signature_b64}"

@router.post("/", response_model=UserSubscriptionResponse)
def create_user_sub(
    data: UserSubscriptionCreate, 
    db: Session = Depends(get_db), 
    current_admin: str = Depends(get_current_admin)
):
    temp_count = db.query(UserSubscription).count() + 1
    unique_token = generate_secure_token(temp_count)
    
    while db.query(UserSubscription).filter(UserSubscription.token == unique_token).first():
        temp_count += 1
        unique_token = generate_secure_token(temp_count)

    user = UserSubscription(
        username=data.username,
        token=unique_token,
        data_limit_mb=0,
        duration_minutes=data.duration_minutes,
        expire_date=None,
        first_use=None,
        is_active=True,
        is_blocked=False,
        group_id=data.group_id if data.group_id else None
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.get("/", response_model=List[UserSubscriptionResponse])
def get_user_subs(
    db: Session = Depends(get_db), 
    current_admin: str = Depends(get_current_admin)
):
    return db.query(UserSubscription).all()

@router.patch("/{user_id}")
def update_user(
    user_id: int,
    data: UserSubscriptionUpdate,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    user = db.query(UserSubscription).filter(UserSubscription.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if data.group_id is not None:
        user.group_id = data.group_id if data.group_id > 0 else None
    if data.duration_minutes is not None:
        user.duration_minutes = data.duration_minutes
    
    db.commit()
    return {"status": "success"}

@router.post("/{user_id}/block")
def block_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    user = db.query(UserSubscription).filter(UserSubscription.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_blocked = True
    db.commit()
    block_user_mappings(db, user_id)
    return {"status": "success"}

@router.post("/{user_id}/unblock")
def unblock_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    user = db.query(UserSubscription).filter(UserSubscription.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_blocked = False
    db.commit()
    unblock_user_mappings(db, user_id)
    return {"status": "success"}

@router.post("/{user_id}/reset")
def reset_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    user = db.query(UserSubscription).filter(UserSubscription.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.first_use = None
    user.expire_date = None
    user.is_active = True
    user.is_blocked = False
    db.commit()
    unblock_user_mappings(db, user_id)
    return {"status": "success"}

@router.delete("/{user_id}")
def delete_user_sub(
    user_id: int, 
    db: Session = Depends(get_db), 
    current_admin: str = Depends(get_current_admin)
):
    user = db.query(UserSubscription).filter(UserSubscription.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User subscription not found")
    
    delete_user_mappings(db, user_id)
    db.delete(user)
    db.commit()
    return {"message": "deleted"}