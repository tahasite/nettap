from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Float, ForeignKey, BigInteger
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from config import BOT_DATABASE_URL

engine = create_engine(BOT_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class TelegramUser(Base):
    __tablename__ = "telegram_users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    phone_number = Column(String, nullable=True, index=True)
    is_joined_channels = Column(Boolean, default=False)
    has_used_test = Column(Boolean, default=False)
    test_sub_token = Column(String, nullable=True)
    referred_by = Column(BigInteger, nullable=True)
    balance = Column(Integer, default=0)
    is_banned = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_telegram_id = Column(BigInteger, ForeignKey("telegram_users.telegram_id"), index=True)
    plan_id = Column(String)
    plan_name = Column(String)
    plan_minutes = Column(Integer)
    plan_price = Column(Integer)
    status = Column(String, default="pending")
    receipt_file_id = Column(String, nullable=True)
    receipt_message_id = Column(Integer, nullable=True)
    admin_note = Column(String, nullable=True)
    sub_username = Column(String, nullable=True)
    sub_token = Column(String, nullable=True)
    sub_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(BigInteger, nullable=True)
    
    user = relationship("TelegramUser", back_populates="orders")

class BotSubscription(Base):
    __tablename__ = "bot_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_telegram_id = Column(BigInteger, index=True)
    sub_username = Column(String, unique=True, index=True)
    sub_token = Column(String, unique=True, index=True)
    sub_url = Column(String)
    plan_id = Column(String)
    duration_minutes = Column(Integer)
    is_test = Column(Boolean, default=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    expire_notified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class BroadcastMessage(Base):
    __tablename__ = "broadcast_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(BigInteger)
    message_text = Column(String)
    total_users = Column(Integer, default=0)
    sent_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_session():
    return SessionLocal()