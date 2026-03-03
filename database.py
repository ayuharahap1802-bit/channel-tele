from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, BigInteger, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json
from config import Config

engine = create_engine(Config.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    language = Column(String(10), default='id')
    is_active = Column(Boolean, default=True)
    joined_at = Column(DateTime, default=datetime.utcnow)
    last_interaction = Column(DateTime, default=datetime.utcnow)
    total_interactions = Column(Integer, default=0)
    
    # Admin fields
    is_admin = Column(Boolean, default=False)
    admin_level = Column(String(50), default='user')  # super_admin, admin, moderator, broadcaster
    permissions = Column(Text, default='{}')  # JSON string of permissions
    
    def get_permissions(self):
        return json.loads(self.permissions) if self.permissions else {}
    
    def set_permissions(self, perms_dict):
        self.permissions = json.dumps(perms_dict)

class AdminLog(Base):
    __tablename__ = 'admin_logs'
    
    id = Column(Integer, primary_key=True)
    admin_id = Column(BigInteger, nullable=False)
    action = Column(String(255), nullable=False)
    details = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(50))

class Broadcast(Base):
    __tablename__ = 'broadcasts'
    
    id = Column(Integer, primary_key=True)
    message_text = Column(Text, nullable=False)
    created_by = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    scheduled_time = Column(DateTime)
    status = Column(String(50), default='pending')  # pending, sending, completed, failed
    total_recipients = Column(Integer, default=0)
    sent_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)

class AutoPost(Base):
    __tablename__ = 'auto_posts'
    
    id = Column(Integer, primary_key=True)
    channel_id = Column(BigInteger, nullable=False)
    message_text = Column(Text, nullable=False)
    schedule_time = Column(String(50))  # Format: "HH:MM"
    schedule_days = Column(String(255))  # JSON array of days (0-6, Monday=0)
    is_active = Column(Boolean, default=True)
    created_by = Column(BigInteger)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_posted = Column(DateTime)

class QuickReply(Base):
    __tablename__ = 'quick_replies'
    
    id = Column(Integer, primary_key=True)
    keyword = Column(String(255), unique=True, nullable=False)
    response = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_by = Column(BigInteger)
    created_at = Column(DateTime, default=datetime.utcnow)

class MessageTemplate(Base):
    __tablename__ = 'message_templates'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(100))
    created_by = Column(BigInteger)
    created_at = Column(DateTime, default=datetime.utcnow)

class Setting(Base):
    __tablename__ = 'settings'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(255), unique=True, nullable=False)
    value = Column(Text)
    description = Column(String(500))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DatabaseBackup(Base):
    __tablename__ = 'database_backups'
    
    id = Column(Integer, primary_key=True)
    filename = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    size = Column(Integer)
    created_by = Column(BigInteger)

# Create tables
Base.metadata.create_all(bind=engine)

# Database helper functions
def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

def init_settings():
    db = SessionLocal()
    default_settings = [
        ('bot_name', 'Telegram Bot', 'Nama bot'),
        ('welcome_message', 'Selamat datang!', 'Pesan selamat datang'),
        ('default_language', 'id', 'Bahasa default'),
        ('broadcast_delay', '1', 'Delay broadcast dalam detik'),
        ('max_broadcast_per_day', '10', 'Maksimal broadcast per hari'),
    ]
    
    for key, value, desc in default_settings:
        setting = db.query(Setting).filter_by(key=key).first()
        if not setting:
            setting = Setting(key=key, value=value, description=desc)
            db.add(setting)
    
    db.commit()
    db.close()
