from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from datetime import datetime
import json
from database import get_db, User, Setting, AdminLog, DatabaseBackup
from config import Config

async def admins_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manage admins"""
    user_id = update.effective_user.id
    
    # Check if super admin
    if user_id not in Config.SUPER_ADMIN_IDS:
        await update.message.reply_text("⛔ This command is for super admins only.")
        return
    
    db = next(get_db())
    
    admins = db.query(User).filter_by(is_admin=True).all()
    
    text = "👑 *Admin Management*\n\n"
    
    if admins:
        text += "*Admin List:*\n"
        for i, admin in enumerate(admins, 1):
            text += f"{i}. {admin.first_name} (@{admin.username or '-'})\n"
            text += f"   Level: {admin.admin_level}\n"
            text += f"   ID: `{admin.user_id}`\n\n"
    else:
        text += "No admins yet.\n\n"
    
    text += f"Super Admin IDs: {', '.join(map(str, Config.SUPER_ADMIN_IDS))}"
    
    db.close()
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View settings"""
    user_id = update.effective_user.id
    
    if user_id not in Config.SUPER_ADMIN_IDS:
        await update.message.reply_text("⛔ This command is for super admins only.")
        return
    
    db = next(get_db())
    
    settings = db.query(Setting).all()
    db.close()
    
    text = "⚙️ *Bot Settings*\n\n"
    
    for setting in settings:
        text += f"• {setting.key}: `{setting.value}`\n"
        text += f"  _{setting.description}_\n\n"
    
    text += "\nUse /set [key] [value] to change"
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def set_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Change setting"""
    user_id = update.effective_user.id
    
    if user_id not in Config.SUPER_ADMIN_IDS:
        await update.message.reply_text("⛔ This command is for super admins only.")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /set [key] [value]")
        return
    
    key = context.args[0]
    value = ' '.join(context.args[1:])
    
    db = next(get_db())
    setting = db.query(Setting).filter_by(key=key).first()
    
    if setting:
        setting.value = value
        setting.updated_at = datetime.utcnow()
        db.commit()
        await update.message.reply_text(f"✅ Setting {key} updated to: {value}")
    else:
        await update.message.reply_text(f"❌ Setting {key} not found")
    
    db.close()

async def backup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Backup database"""
    user_id = update.effective_user.id
    
    if user_id not in Config.SUPER_ADMIN_IDS:
        await update.message.reply_text("⛔ This command is for super admins only.")
        return
    
    try:
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"backup_{timestamp}.db"
        
        db = next(get_db())
        
        backup = DatabaseBackup(
            filename=filename,
            created_at=datetime.utcnow(),
            created_by=user_id,
            size=0
        )
        db.add(backup)
        db.commit()
        db.close()
        
        await update.message.reply_text(
            f"✅ *Database Backup Created*\n\n"
            f"Filename: `{filename}`\n"
            f"Time: {timestamp}",
            parse_mode='Markdown'
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Backup failed: {str(e)}")

def setup_superadmin_handlers(app):
    """Setup super admin handlers"""
    app.add_handler(CommandHandler("admins", admins_command))
    app.add_handler(CommandHandler("settings", settings_command))
    app.add_handler(CommandHandler("set", set_command))
    app.add_handler(CommandHandler("backup", backup_command))
