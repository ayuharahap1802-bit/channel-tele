from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from database import get_db, User
import json

def get_user_level(user_id):
    db = next(get_db())
    user = db.query(User).filter_by(user_id=user_id).first()
    return user.admin_level if user and user.is_admin else 'user'

def admin_required(level='admin'):
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user_id = update.effective_user.id
            
            # Check if super admin
            from config import Config
            if user_id in Config.SUPER_ADMIN_IDS:
                return await func(update, context, *args, **kwargs)
            
            db = next(get_db())
            user = db.query(User).filter_by(user_id=user_id).first()
            
            if not user or not user.is_admin:
                await update.message.reply_text("⛔ Anda tidak memiliki akses ke perintah ini.")
                return
            
            # Check permission level
            level_order = {
                'super_admin': 4,
                'admin': 3,
                'moderator': 2,
                'broadcaster': 1,
                'user': 0
            }
            
            if level_order.get(user.admin_level, 0) < level_order.get(level, 3):
                await update.message.reply_text("⛔ Level admin Anda tidak mencukupi.")
                return
            
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator

def permission_required(permission):
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user_id = update.effective_user.id
            
            # Check if super admin
            from config import Config
            if user_id in Config.SUPER_ADMIN_IDS:
                return await func(update, context, *args, **kwargs)
            
            db = next(get_db())
            user = db.query(User).filter_by(user_id=user_id).first()
            
            if not user or not user.is_admin:
                await update.message.reply_text("⛔ Anda tidak memiliki akses ke perintah ini.")
                return
            
            permissions = user.get_permissions()
            if not permissions.get(permission, False):
                await update.message.reply_text(f"⛔ Anda tidak memiliki izin: {permission}")
                return
            
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator

def log_activity(action):
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            result = await func(update, context, *args, **kwargs)
            
            # Log activity
            from database import AdminLog, get_db
            db = next(get_db())
            
            log = AdminLog(
                admin_id=update.effective_user.id,
                action=action,
                details=f"Performed by {update.effective_user.username or update.effective_user.first_name}"
            )
            db.add(log)
            db.commit()
            
            return result
        return wrapper
    return decorator

def feature_enabled(feature_name):
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            from config import Config
            if not Config.FEATURES.get(feature_name, True):
                await update.message.reply_text("⚠️ Fitur ini sedang dinonaktifkan.")
                return
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator

def track_user(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if update.effective_user and not update.effective_user.is_bot:
            from config import Config
            if Config.FEATURES.get('user_tracking', True):
                db = next(get_db())
                user = db.query(User).filter_by(user_id=update.effective_user.id).first()
                
                if not user:
                    user = User(
                        user_id=update.effective_user.id,
                        username=update.effective_user.username,
                        first_name=update.effective_user.first_name,
                        last_name=update.effective_user.last_name,
                        language=update.effective_user.language_code or 'id'
                    )
                    db.add(user)
                
                user.last_interaction = datetime.utcnow()
                user.total_interactions += 1
                db.commit()
        
        return await func(update, context, *args, **kwargs)
    return wrapper
