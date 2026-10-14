from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Any

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class AdminLogin(BaseModel):
    username: str
    password: str

class SellerSubscriptionCreate(BaseModel):
    name: str
    url: str

class SellerSubscriptionResponse(BaseModel):
    id: int
    name: str
    url: str
    is_active: bool
    last_updated: Optional[datetime] = None
    class Config:
        from_attributes = True

class UserSubscriptionCreate(BaseModel):
    username: str
    duration_minutes: int = 43200
    group_id: Optional[int] = None

class UserSubscriptionUpdate(BaseModel):
    group_id: Optional[int] = None
    duration_minutes: Optional[int] = None

class UserSubscriptionResponse(BaseModel):
    id: int
    username: str
    token: str
    is_active: bool
    is_blocked: bool
    data_limit_mb: float
    data_used_mb: float
    duration_minutes: int
    expire_date: Optional[datetime] = None
    first_use: Optional[datetime] = None
    group_id: Optional[int] = None
    created_at: datetime
    class Config:
        from_attributes = True

class ConfigGroupCreate(BaseModel):
    name: str
    description: str = ""
    color: str = "#6366f1"

class ConfigGroupResponse(BaseModel):
    id: int
    name: str
    description: str
    color: str
    created_at: datetime
    config_count: int = 0
    user_count: int = 0
    class Config:
        from_attributes = True

class GroupConfigAssign(BaseModel):
    config_ids: List[int]

class CronJobLogResponse(BaseModel):
    id: int
    job_name: str
    status: str
    message: str
    duration_ms: int
    executed_at: datetime
    class Config:
        from_attributes = True

class BotPlanCreate(BaseModel):
    plan_key: str
    name: str
    emoji: str = "📦"
    duration_minutes: int
    price: int = 0
    group_id: Optional[int] = None
    is_active: bool = True
    is_test: bool = False
    display_order: int = 0

class BotPlanUpdate(BaseModel):
    name: Optional[str] = None
    emoji: Optional[str] = None
    duration_minutes: Optional[int] = None
    price: Optional[int] = None
    group_id: Optional[int] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None

class BotPlanResponse(BaseModel):
    id: int
    plan_key: str
    name: str
    emoji: str
    duration_minutes: int
    price: int
    group_id: Optional[int] = None
    group_name: Optional[str] = None
    is_active: bool
    is_test: bool
    display_order: int
    created_at: datetime
    class Config:
        from_attributes = True

class SettingResponse(BaseModel):
    id: int
    key: str
    value: str
    category: str
    value_type: str
    label_en: str
    label_fa: str
    description_en: str
    description_fa: str
    is_public: bool
    is_secret: bool
    display_order: int
    updated_at: datetime
    class Config:
        from_attributes = True

class SettingUpdate(BaseModel):
    value: str

class SettingBulkUpdate(BaseModel):
    settings: dict

class SettingsCategoryResponse(BaseModel):
    category: str
    label_en: str
    label_fa: str
    icon: str
    settings: List[SettingResponse]