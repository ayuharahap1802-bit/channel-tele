from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from datetime import datetime, timedelta
import random
from database import get_db, User, Broadcast, AutoPost
from config import Config

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command"""
    user = update.effective_user
    
    # Track user
    if Config.FEATURES.get('user_tracking', True):
        db = next(get_db())
        db_user = db.query(User).filter_by(user_id=user.id).first()
        
        if not db_user:
            db_user = User(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name or '',
                language=user.language_code or 'id'
            )
            db.add(db_user)
        else:
            db_user.last_interaction = datetime.utcnow()
            db_user.total_interactions += 1
        
        db.commit()
        db.close()
    
    welcome_text = f"""👋 *Welcome, {user.first_name}!*

I am a multi-functional bot with various advanced features.

*Available Commands:*
/help - Show help
/info - Your account info
/stats - Bot statistics
/promo - Latest promos"""
    
    keyboard = [
        [InlineKeyboardButton("📋 Help", callback_data="help"),
         InlineKeyboardButton("ℹ️ Info", callback_data="info")],
        [InlineKeyboardButton("📊 Stats", callback_data="stats"),
         InlineKeyboardButton("🎉 Promo", callback_data="promo")],
    ]
    
    if user.id in Config.SUPER_ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("👑 Admin Panel", callback_data="admin")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command"""
    help_text = """📋 *Bot Help*

*Public Commands:*
/start - Start bot
/help - This help
/info - Account info
/promo - View promos
/stats - Bot stats

*Admin Commands:*
/admin - Admin dashboard
/users - Manage users
/broadcast - Send broadcast
/posts - Manage auto posts"""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Info command"""
    user = update.effective_user
    
    db = next(get_db())
    db_user = db.query(User).filter_by(user_id=user.id).first()
    db.close()
    
    info_text = f"""📊 *Account Information*

🆔 ID: `{user.id}`
👤 Username: @{user.username or '-'}
📝 Name: {user.first_name} {user.last_name or ''}
🗣 Language: {user.language_code or 'id'}
📅 Joined: {db_user.joined_at.strftime('%d/%m/%Y') if db_user else '-'}
🔄 Interactions: {db_user.total_interactions if db_user else 0}"""
    
    await update.message.reply_text(info_text, parse_mode='Markdown')

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stats command"""
    db = next(get_db())
    
    total_users = db.query(User).count()
    active_today = db.query(User).filter(
        User.last_interaction >= datetime.utcnow() - timedelta(days=1)
    ).count()
    total_posts = db.query(AutoPost).count()
    total_broadcasts = db.query(Broadcast).count()
    
    db.close()
    
    stats_text = f"""📈 *Bot Statistics*

👥 Total Users: {total_users:,}
📊 Active Today: {active_today:,}
📝 Total Posts: {total_posts}
📨 Total Broadcasts: {total_broadcasts}
⚡️ Status: ✅ Online"""
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')

async def promo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Promo command"""
    promos = """🎉 *Latest Promos*

• Discount 50% for all products
• Free shipping min. 100k
• 10% cashback bonus
• Buy 1 get 1 free weekend"""
    
    await update.message.reply_text(promos, parse_mode='Markdown')

async def handle_quick_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle quick replies"""
    if not update.message or not update.message.text:
        return
    
    text = update.message.text.lower()
    db = next(get_db())
    
    from database import QuickReply
    quick_reply = db.query(QuickReply).filter_by(keyword=text, is_active=True).first()
    db.close()
    
    if quick_reply:
        await update.message.reply_text(quick_reply.response)

async def handle_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle new members"""
    if not Config.FEATURES.get('auto_welcome', True):
        return
    
    for new_member in update.message.new_chat_members:
        if new_member.is_bot:
            continue
        
        chat_id = update.effective_chat.id
        if chat_id in Config.WELCOME_CHANNELS:
            welcome_msgs = [
                f"Selamat datang {new_member.first_name} di channel kami! 🎉",
                f"Halo {new_member.first_name}, senang kamu bergabung! 👋",
                f"Welcome {new_member.first_name}! Semoga betah di sini 😊"
            ]
            welcome_msg = random.choice(welcome_msgs)
            
            await update.message.reply_text(welcome_msg)

def setup_public_handlers(app):
    """Setup public handlers"""
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("info", info_command))
    app.add_handler(CommandHandler("promo", promo_command))
    app.add_handler(CommandHandler("stats", stats_command))
    
    # Handle quick replies
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_quick_reply))
    
    # Handle new members
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_new_member))
