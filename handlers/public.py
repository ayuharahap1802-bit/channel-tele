from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from datetime import datetime, timedelta
from database import get_db, User, Broadcast, AutoPost
from utils.decorators import track_user, feature_enabled
from utils.helpers import get_text, format_number
from config import Config
import random

@track_user
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Welcome message
    welcome_text = get_text(user.id, "welcome", name=user.first_name)
    
    # Create keyboard
    keyboard = [
        [InlineKeyboardButton("📋 Bantuan", callback_data="help"),
         InlineKeyboardButton("ℹ️ Info", callback_data="info")],
        [InlineKeyboardButton("📊 Statistik", callback_data="stats"),
         InlineKeyboardButton("🎉 Promo", callback_data="promo")],
    ]
    
    if user.id in Config.SUPER_ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("👑 Admin Panel", callback_data="admin")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

@track_user
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = get_text(update.effective_user.id, "help")
    await update.message.reply_text(help_text, parse_mode='Markdown')

@track_user
async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = next(get_db())
    
    db_user = db.query(User).filter_by(user_id=user.id).first()
    
    info_text = get_text(user.id, "info",
        user_id=user.id,
        username=user.username or "-",
        first_name=user.first_name,
        last_name=user.last_name or "",
        language=db_user.language if db_user else "id",
        joined_at=db_user.joined_at.strftime("%d/%m/%Y") if db_user else "-",
        interactions=db_user.total_interactions if db_user else 0
    )
    
    await update.message.reply_text(info_text, parse_mode='Markdown')

@track_user
async def promo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Sample promos - bisa diambil dari database
    promos = "• Diskon 50% untuk semua produk\n• Gratis ongkir minimal belanja 100k\n• Bonus cashback 10%"
    
    promo_text = get_text(update.effective_user.id, "promo", promos=promos)
    await update.message.reply_text(promo_text, parse_mode='Markdown')

@track_user
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = next(get_db())
    
    total_users = db.query(User).count()
    active_today = db.query(User).filter(
        User.last_interaction >= datetime.utcnow() - timedelta(days=1)
    ).count()
    total_posts = db.query(AutoPost).count()
    total_broadcasts = db.query(Broadcast).count()
    
    stats_text = get_text(update.effective_user.id, "stats",
        total_users=format_number(total_users),
        active_today=format_number(active_today),
        total_posts=format_number(total_posts),
        total_broadcasts=format_number(total_broadcasts),
        status="✅ Online"
    )
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')

async def handle_quick_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle quick replies based on keywords"""
    if not update.message or not update.message.text:
        return
    
    text = update.message.text.lower()
    db = next(get_db())
    
    from database import QuickReply
    quick_reply = db.query(QuickReply).filter_by(keyword=text, is_active=True).first()
    
    if quick_reply:
        await update.message.reply_text(quick_reply.response)

async def handle_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle new members joining channel/group"""
    if not Config.FEATURES.get('auto_welcome', True):
        return
    
    for new_member in update.message.new_chat_members:
        if new_member.is_bot:
            continue
        
        # Check if this channel is in welcome channels
        chat_id = update.effective_chat.id
        if chat_id in Config.WELCOME_CHANNELS:
            # Get random welcome message
            from templates.messages import welcome_templates
            welcome_msg = random.choice(welcome_templates).format(name=new_member.first_name)
            
            await update.message.reply_text(welcome_msg)

def setup_public_handlers(app):
    """Setup public command handlers"""
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("info", info_command))
    app.add_handler(CommandHandler("promo", promo_command))
    app.add_handler(CommandHandler("stats", stats_command))
    
    # Handle quick replies
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_quick_reply))
    
    # Handle new members
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_new_member))
