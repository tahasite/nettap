from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import ConfigGroup, ExtractedConfig, UserSubscription
from app.schemas import ConfigGroupCreate, ConfigGroupResponse, GroupConfigAssign
from app.utils.deps import get_current_admin

router = APIRouter(prefix="/api/groups", tags=["groups"])

@router.get("/", response_model=List[ConfigGroupResponse])
def get_groups(
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    groups = db.query(ConfigGroup).all()
    result = []
    for g in groups:
        result.append(ConfigGroupResponse(
            id=g.id,
            name=g.name,
            description=g.description,
            color=g.color,
            created_at=g.created_at,
            config_count=len(g.configs),
            user_count=len(g.users)
        ))
    return result

@router.post("/", response_model=ConfigGroupResponse)
def create_group(
    data: ConfigGroupCreate,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    existing = db.query(ConfigGroup).filter(ConfigGroup.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Group name already exists")
    
    group = ConfigGroup(name=data.name, description=data.description, color=data.color)
    db.add(group)
    db.commit()
    db.refresh(group)
    return ConfigGroupResponse(
        id=group.id, name=group.name, description=group.description,
        color=group.color, created_at=group.created_at, config_count=0, user_count=0
    )

@router.get("/{group_id}/configs")
def get_group_configs(
    group_id: int,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    group = db.query(ConfigGroup).filter(ConfigGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return [{"id": c.id, "name": c.name, "country_flag": c.country_flag} for c in group.configs]

@router.post("/{group_id}/assign-configs")
def assign_configs_to_group(
    group_id: int,
    data: GroupConfigAssign,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    group = db.query(ConfigGroup).filter(ConfigGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    group.configs.clear()
    db.commit()
    
    configs = db.query(ExtractedConfig).filter(ExtractedConfig.id.in_(data.config_ids)).all()
    for c in configs:
        group.configs.append(c)
    db.commit()
    
    return {"status": "success", "assigned": len(configs)}

@router.delete("/{group_id}")
def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    group = db.query(ConfigGroup).filter(ConfigGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    db.query(UserSubscription).filter(UserSubscription.group_id == group_id).update({"group_id": None})
    db.delete(group)
    db.commit()
    return {"status": "success"}