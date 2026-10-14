from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import BotPlan, ConfigGroup
from app.schemas import BotPlanCreate, BotPlanUpdate, BotPlanResponse
from app.utils.deps import get_current_admin

router = APIRouter(prefix="/api/plans", tags=["plans"])

def enrich_plan(plan: BotPlan, db: Session) -> BotPlanResponse:
    group_name = None
    if plan.group_id:
        group = db.query(ConfigGroup).filter(ConfigGroup.id == plan.group_id).first()
        if group:
            group_name = group.name
    
    return BotPlanResponse(
        id=plan.id,
        plan_key=plan.plan_key,
        name=plan.name,
        emoji=plan.emoji,
        duration_minutes=plan.duration_minutes,
        price=plan.price,
        group_id=plan.group_id,
        group_name=group_name,
        is_active=plan.is_active,
        is_test=plan.is_test,
        display_order=plan.display_order,
        created_at=plan.created_at
    )

@router.get("/", response_model=List[BotPlanResponse])
def list_plans(
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    plans = db.query(BotPlan).order_by(BotPlan.display_order, BotPlan.id).all()
    return [enrich_plan(p, db) for p in plans]

@router.get("/public")
def list_public_plans(db: Session = Depends(get_db)):
    plans = db.query(BotPlan).filter(BotPlan.is_active == True).order_by(BotPlan.display_order, BotPlan.id).all()
    return [{
        "plan_key": p.plan_key,
        "name": p.name,
        "emoji": p.emoji,
        "duration_minutes": p.duration_minutes,
        "price": p.price,
        "group_id": p.group_id,
        "is_test": p.is_test,
        "display_order": p.display_order
    } for p in plans]

@router.post("/", response_model=BotPlanResponse)
def create_plan(
    data: BotPlanCreate,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    existing = db.query(BotPlan).filter(BotPlan.plan_key == data.plan_key).first()
    if existing:
        raise HTTPException(status_code=400, detail="Plan key already exists")
    
    plan = BotPlan(
        plan_key=data.plan_key,
        name=data.name,
        emoji=data.emoji,
        duration_minutes=data.duration_minutes,
        price=data.price,
        group_id=data.group_id if data.group_id else None,
        is_active=data.is_active,
        is_test=data.is_test,
        display_order=data.display_order
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return enrich_plan(plan, db)

@router.patch("/{plan_id}", response_model=BotPlanResponse)
def update_plan(
    plan_id: int,
    data: BotPlanUpdate,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    plan = db.query(BotPlan).filter(BotPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        if key == "group_id":
            plan.group_id = value if value and value > 0 else None
        else:
            setattr(plan, key, value)
    
    db.commit()
    db.refresh(plan)
    return enrich_plan(plan, db)

@router.delete("/{plan_id}")
def delete_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    plan = db.query(BotPlan).filter(BotPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    db.delete(plan)
    db.commit()
    return {"status": "success"}

@router.post("/seed-defaults")
def seed_default_plans(
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    defaults = [
        {"plan_key": "test", "name": "تست رایگان", "emoji": "🎁", "duration_minutes": 15, "price": 0, "is_test": True, "display_order": 0},
        {"plan_key": "24h", "name": "24 ساعته", "emoji": "⚡", "duration_minutes": 1440, "price": 5000, "display_order": 1},
        {"plan_key": "7d", "name": "7 روزه", "emoji": "📅", "duration_minutes": 10080, "price": 25000, "display_order": 2},
        {"plan_key": "30d", "name": "30 روزه", "emoji": "🔥", "duration_minutes": 43200, "price": 60000, "display_order": 3},
        {"plan_key": "60d", "name": "60 روزه", "emoji": "💎", "duration_minutes": 86400, "price": 100000, "display_order": 4},
        {"plan_key": "90d", "name": "90 روزه", "emoji": "👑", "duration_minutes": 129600, "price": 130000, "display_order": 5},
    ]
    
    created = 0
    for default in defaults:
        existing = db.query(BotPlan).filter(BotPlan.plan_key == default["plan_key"]).first()
        if not existing:
            plan = BotPlan(**default)
            db.add(plan)
            created += 1
    db.commit()
    return {"status": "success", "created": created}