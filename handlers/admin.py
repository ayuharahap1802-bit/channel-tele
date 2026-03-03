from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from datetime import datetime, timedelta
from database import get_db, User, Broadcast, AutoPost, AdminLog, QuickReply
from config import Config

async def admin_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin dashboard"""
    user = update.effective_user
    
    # Check if admin
    if user.id not in Config.SUPER_ADMIN_IDS:
        db = next(get_db())
        db_user = db.query(User).filter_by(user_id=user.id).first()
        db.close()
        
        if not db_user or not db_user.is_admin:
            await update.message.reply_text("⛔ You don't have access to this command.")
            return
    
    db = next(get_db())
    total_users = db.query(User).count()
    pending_broadcasts = db.query(Broadcast).filter_by(status='pending').count()
    total_posts = db.query(AutoPost).count()
    db.close()
    
    dashboard_text = f"""👑 *Admin Dashboard*

Welcome, {user.first_name}

📊 *Quick Stats:*
👥 Total Users: {total_users:,}
📨 Pending Broadcasts: {pending_broadcasts}
📝 Auto Posts: {total_posts}

🔧 *Admin Menu:*
👥 /users - Manage Users
📨 /broadcast - Broadcast Message
📝 /posts - Manage Auto Posts
📊 /admin_stats - Full Statistics
📋 /logs - Activity Logs
💬 /quick_replies - Quick Replies"""
    
    keyboard = [
        [InlineKeyboardButton("👥 Users", callback_data="admin_users"),
         InlineKeyboardButton("📨 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("📝 Posts", callback_data="admin_posts"),
         InlineKeyboardButton("📊 Stats", callback_data="admin_stats")],
        [InlineKeyboardButton("📋 Logs", callback_data="admin_logs")],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(dashboard_text, parse_mode='Markdown', reply_markup=reply_markup)

async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List users"""
    db = next(get_db())
    
    page = 1
    per_page = 10
    offset = (page - 1) * per_page
    
    total_users = db.query(User).count()
    users = db.query(User).order_by(User.joined_at.desc()).limit(per_page).offset(offset).all()
    db.close()
    
    text = f"👥 *Users List (Page {page})*\n\n"
    text += f"Total: {total_users:,} users\n\n"
    
    for i, user in enumerate(users, 1):
        status = "👑" if user.is_admin else "👤"
        text += f"{i}. {status} {user.first_name} (@{user.username or '-'})\n"
        text += f"   ID: `{user.user_id}`\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start broadcast"""
    if not Config.FEATURES.get('broadcast', True):
        await update.message.reply_text("⚠️ Broadcast feature is disabled.")
        return
    
    context.user_data['broadcast_step'] = 'waiting_message'
    
    text = """📨 *Broadcast Message*

Please send the message you want to broadcast.

Type /cancel to cancel."""
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def posts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manage auto posts"""
    if not Config.FEATURES.get('auto_post', True):
        await update.message.reply_text("⚠️ Auto post feature is disabled.")
        return
    
    db = next(get_db())
    posts = db.query(AutoPost).filter_by(is_active=True).all()
    db.close()
    
    text = "📝 *Auto Post Management*\n\n"
    
    if posts:
        for i, post in enumerate(posts, 1):
            text += f"{i}. Channel: `{post.channel_id}`\n"
            text += f"   Time: {post.schedule_time}\n"
    else:
        text += "No scheduled auto posts.\n"
    
    keyboard = [
        [InlineKeyboardButton("➕ Create Post", callback_data="post_create")],
        [InlineKeyboardButton("📅 View Schedule", callback_data="post_schedule")],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)

async def admin_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin statistics"""
    db = next(get_db())
    
    total_users = db.query(User).count()
    active_today = db.query(User).filter(
        User.last_interaction >= datetime.utcnow() - timedelta(days=1)
    ).count()
    active_week = db.query(User).filter(
        User.last_interaction >= datetime.utcnow() - timedelta(days=7)
    ).count()
    admins = db.query(User).filter_by(is_admin=True).count()
    
    total_broadcasts = db.query(Broadcast).count()
    successful_broadcasts = db.query(Broadcast).filter_by(status='completed').count()
    total_posts = db.query(AutoPost).count()
    
    db.close()
    
    text = f"""📊 *Complete Bot Statistics*

👥 *User Statistics:*
• Total Users: {total_users:,}
• Active Today: {active_today:,}
• Active This Week: {active_week:,}
• Total Admins: {admins}

📨 *Broadcast Statistics:*
• Total Broadcasts: {total_broadcasts}
• Successful: {successful_broadcasts}

📝 *Auto Post Statistics:*
• Total Posts: {total_posts}

🕐 Last Updated: {datetime.utcnow().strftime('%d/%m/%Y %H:%M:%S')} UTC"""
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View activity logs"""
    db = next(get_db())
    
    logs = db.query(AdminLog).order_by(AdminLog.timestamp.desc()).limit(20).all()
    db.close()
    
    text = "📋 *Activity Logs (Last 20)*\n\n"
    
    if logs:
        for log in logs:
            time_str = log.timestamp.strftime('%d/%m %H:%M')
            text += f"• [{time_str}] `{log.admin_id}`: {log.action}\n"
    else:
        text += "No logs yet."
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def quick_replies_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manage quick replies"""
    db = next(get_db())
    
    replies = db.query(QuickReply).filter_by(is_active=True).all()
    db.close()
    
    text = "💬 *Quick Replies*\n\n"
    
    if replies:
        for reply in replies:
            text += f"• {reply.keyword}: {reply.response[:50]}...\n"
    else:
        text += "No quick replies configured."
    
    keyboard = [
        [InlineKeyboardButton("➕ Add Reply", callback_data="qr_add")],
        [InlineKeyboardButton("❌ Delete Reply", callback_data="qr_delete")],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)

async def handle_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle broadcast message input"""
    if 'broadcast_step' not in context.user_data:
        return
    
    if context.user_data['broadcast_step'] == 'waiting_message':
        context.user_data['broadcast_message'] = update.message.text
        context.user_data['broadcast_step'] = 'waiting_confirmation'
        
        text = f"""📨 *Preview Broadcast*

{update.message.text}

*Options:*
/confirm - Send now
/cancel - Cancel"""
        
        await update.message.reply_text(text, parse_mode='Markdown')

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "admin_users":
        await users_command(update, context)
    elif query.data == "admin_stats":
        await admin_stats_command(update, context)
    elif query.data == "admin_logs":
        await logs_command(update, context)

def setup_admin_handlers(app):
    """Setup admin handlers"""
    app.add_handler(CommandHandler("admin", admin_dashboard))
    app.add_handler(CommandHandler("users", users_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(CommandHandler("posts", posts_command))
    app.add_handler(CommandHandler("admin_stats", admin_stats_command))
    app.add_handler(CommandHandler("logs", logs_command))
    app.add_handler(CommandHandler("quick_replies", quick_replies_command))
    
    # Handle callbacks
    app.add_handler(CallbackQueryHandler(button_callback))
    
    # Handle broadcast message input
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_broadcast_message
    ))
