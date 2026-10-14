from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, UniqueConstraint, Table, Text
from sqlalchemy.orm import relationship
from app.database import Base

group_configs = Table(
    'group_configs',
    Base.metadata,
    Column('group_id', Integer, ForeignKey('config_groups.id', ondelete='CASCADE')),
    Column('config_id', Integer, ForeignKey('extracted_configs.id', ondelete='CASCADE')),
    UniqueConstraint('group_id', 'config_id', name='unique_group_config')
)

class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class SellerSubscription(Base):
    __tablename__ = "seller_subscriptions"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    url = Column(String, unique=True)
    is_active = Column(Boolean, default=True)
    last_updated = Column(DateTime, nullable=True)
    configs = relationship("ExtractedConfig", back_populates="seller_sub", cascade="all, delete-orphan")

class ConfigGroup(Base):
    __tablename__ = "config_groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, default="")
    color = Column(String, default="#6366f1")
    created_at = Column(DateTime, default=datetime.utcnow)
    configs = relationship("ExtractedConfig", secondary=group_configs, back_populates="groups")
    users = relationship("UserSubscription", back_populates="group")

class UserSubscription(Base):
    __tablename__ = "user_subscriptions"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    token = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    is_blocked = Column(Boolean, default=False)
    data_limit_mb = Column(Float, default=0.0)
    data_used_mb = Column(Float, default=0.0)
    duration_minutes = Column(Integer, default=43200)
    expire_date = Column(DateTime, nullable=True)
    first_use = Column(DateTime, nullable=True)
    group_id = Column(Integer, ForeignKey("config_groups.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    group = relationship("ConfigGroup", back_populates="users")
    domain_mappings = relationship("DomainMapping", back_populates="user", cascade="all, delete-orphan")

class ExtractedConfig(Base):
    __tablename__ = "extracted_configs"
    id = Column(Integer, primary_key=True, index=True)
    seller_sub_id = Column(Integer, ForeignKey("seller_subscriptions.id"))
    raw_config = Column(String)
    name = Column(String)
    protocol = Column(String)
    resolved_ip = Column(String, nullable=True)
    country_code = Column(String, default="XX")
    country_flag = Column(String, default="🌍")
    ping = Column(Integer, default=-1)
    is_working = Column(Boolean, default=True)
    is_pinned = Column(Boolean, default=False)
    last_checked = Column(DateTime, default=datetime.utcnow)
    seller_sub = relationship("SellerSubscription", back_populates="configs")
    groups = relationship("ConfigGroup", secondary=group_configs, back_populates="configs")

class DomainMapping(Base):
    __tablename__ = "domain_mappings"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user_subscriptions.id"))
    subdomain = Column(String, unique=True, index=True)
    original_host = Column(String, index=True)
    resolved_ip = Column(String)
    is_active = Column(Boolean, default=True)
    last_ip_check = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("UserSubscription", back_populates="domain_mappings")
    __table_args__ = (UniqueConstraint('user_id', 'original_host', name='unique_user_host'),)

class CronJobLog(Base):
    __tablename__ = "cron_job_logs"
    id = Column(Integer, primary_key=True, index=True)
    job_name = Column(String, index=True)
    status = Column(String, default="success")
    message = Column(String, default="")
    duration_ms = Column(Integer, default=0)
    executed_at = Column(DateTime, default=datetime.utcnow)

class BotPlan(Base):
    __tablename__ = "bot_plans"
    id = Column(Integer, primary_key=True, index=True)
    plan_key = Column(String, unique=True, index=True)
    name = Column(String)
    emoji = Column(String, default="📦")
    duration_minutes = Column(Integer)
    price = Column(Integer, default=0)
    group_id = Column(Integer, ForeignKey("config_groups.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    is_test = Column(Boolean, default=False)
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    group = relationship("ConfigGroup")

class Setting(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    value = Column(Text, default="")
    category = Column(String, index=True, default="general")
    value_type = Column(String, default="text")
    label_en = Column(String, default="")
    label_fa = Column(String, default="")
    description_en = Column(Text, default="")
    description_fa = Column(Text, default="")
    is_public = Column(Boolean, default=False)
    is_secret = Column(Boolean, default=False)
    display_order = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)