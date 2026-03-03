from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from datetime import datetime, timedelta
import asyncio
from database import get_db, User, Broadcast, AutoPost, AdminLog, QuickReply, MessageTemplate
from utils.decorators import admin_required, permission_required, log_activity, feature_enabled
from utils.helpers import get_text, format_number, chunk_list
from config import Config

@admin_required()
@log_activity('view_dashboard')
async def admin_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = next(get_db())
    
    db_user = db.query(User).filter_by(user_id=user.id).first()
    
    # Get stats
    total_users = db.query(User).count()
    pending_broadcasts = db.query(Broadcast).filter_by(status='pending').count()
    total_posts = db.query(AutoPost).count()
    
    dashboard_text = f"""👑 *Admin Dashboard*

Selamat datang, {user.first_name}
Level: {db_user.admin_level if db_user else 'admin'}

📊 *Statistik Cepat:*
👥 Total User: {format_number(total_users)}
📨 Broadcast Pending: {pending_broadcasts}
📝 Auto Posts: {total_posts}

🔧 *Menu Admin:*
👥 /users - Kelola User
📨 /broadcast - Broadcast Message
📝 /posts - Kelola Auto Post
⚙️ /settings - Pengaturan Bot
📊 /admin_stats - Statistik Lengkap
📋 /logs - Activity Logs
🔑 /permissions - Kelola Izin
💬 /quick_replies - Balasan Cepat
📁 /templates - Template Pesan
"""
    
    keyboard = [
        [InlineKeyboardButton("👥 Users", callback_data="admin_users"),
         InlineKeyboardButton("📨 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("📝 Auto Posts", callback_data="admin_posts"),
         InlineKeyboardButton("⚙️ Settings", callback_data="admin_settings")],
        [InlineKeyboardButton("📊 Stats", callback_data="admin_stats"),
         InlineKeyboardButton("📋 Logs", callback_data="admin_logs")],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(dashboard_text, parse_mode='Markdown', reply_markup=reply_markup)

@admin_required()
@permission_required('can_manage_users')
@log_activity('view_users')
async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = next(get_db())
    
    # Pagination
    page = int(context.args[0]) if context.args and context.args[0].isdigit() else 1
    per_page = 10
    offset = (page - 1) * per_page
    
    total_users = db.query(User).count()
    users = db.query(User).order_by(User.joined_at.desc()).limit(per_page).offset(offset).all()
    
    text = f"👥 *Daftar User (Halaman {page})*\n\n"
    text += f"Total: {format_number(total_users)} user\n\n"
    
    for i, user in enumerate(users, 1):
        status = "👑" if user.is_admin else "👤"
        text += f"{i}. {status} {user.first_name} (@{user.username or '-'})\n"
        text += f"   ID: `{user.user_id}` | Joined: {user.joined_at.strftime('%d/%m/%Y')}\n"
        text += f"   Interactions: {user.total_interactions}\n\n"
    
    # Navigation buttons
    keyboard = []
    nav_buttons = []
    
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"users_page_{page-1}"))
    if offset + per_page < total_users:
        nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"users_page_{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.append([InlineKeyboardButton("🔍 Search User", callback_data="users_search")])
    keyboard.append([InlineKeyboardButton("📊 User Stats", callback_data="users_stats")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)

@admin_required()
@permission_required('can_broadcast')
@feature_enabled('broadcast')
@log_activity('start_broadcast')
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start broadcast process"""
    context.user_data['broadcast_step'] = 'waiting_message'
    
    text = """📨 *Broadcast Message*

Silakan kirim pesan yang ingin di-broadcast.

Kamu bisa menggunakan:
• Teks biasa
• Markdown formatting
• Media (foto/video)

Ketik /cancel untuk membatalkan."""
    
    await update.message.reply_text(text, parse_mode='Markdown')

@admin_required()
@permission_required('can_manage_posts')
@feature_enabled('auto_post')
@log_activity('manage_posts')
async def posts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = next(get_db())
    
    posts = db.query(AutoPost).filter_by(is_active=True).all()
    
    text = "📝 *Auto Post Management*\n\n"
    
    if posts:
        for i, post in enumerate(posts, 1):
            text += f"{i}. Channel: `{post.channel_id}`\n"
            text += f"   Waktu: {post.schedule_time}\n"
            text += f"   Status: {'✅ Active' if post.is_active else '❌ Inactive'}\n\n"
    else:
        text += "Belum ada auto post terjadwal.\n"
    
    keyboard = [
        [InlineKeyboardButton("➕ Buat Auto Post", callback_data="post_create")],
        [InlineKeyboardButton("📅 Lihat Jadwal", callback_data="post_schedule")],
        [InlineKeyboardButton("❌ Hapus Post", callback_data="post_delete")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)

@admin_required()
async def admin_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = next(get_db())
    
    # User stats
    total_users = db.query(User).count()
    active_today = db.query(User).filter(
        User.last_interaction >= datetime.utcnow() - timedelta(days=1)
    ).count()
    active_week = db.query(User).filter(
        User.last_interaction >= datetime.utcnow() - timedelta(days=7)
    ).count()
    admins = db.query(User).filter_by(is_admin=True).count()
    
    # Broadcast stats
    total_broadcasts = db.query(Broadcast).count()
    successful_broadcasts = db.query(Broadcast).filter_by(status='completed').count()
    
    # Post stats
    total_posts = db.query(AutoPost).count()
    active_posts = db.query(AutoPost).filter_by(is_active=True).count()
    
    # Activity stats
    today_logs = db.query(AdminLog).filter(
        AdminLog.timestamp >= datetime.utcnow() - timedelta(days=1)
    ).count()
    
    text = f"""📊 *Statistik Lengkap Bot*

👥 *User Statistics:*
• Total Users: {format_number(total_users)}
• Active Today: {format_number(active_today)}
• Active This Week: {format_number(active_week)}
• Total Admins: {admins}

📨 *Broadcast Statistics:*
• Total Broadcasts: {format_number(total_broadcasts)}
• Successful: {format_number(successful_broadcasts)}
• Success Rate: {(successful_broadcasts/total_broadcasts*100) if total_broadcasts > 0 else 0:.1f}%

📝 *Auto Post Statistics:*
• Total Posts: {total_posts}
• Active Posts: {active_posts}

📋 *Activity Statistics:*
• Logs Today: {today_logs}

🕐 *Last Updated:* {datetime.utcnow().strftime('%d/%m/%Y %H:%M:%S')} UTC
"""
    
    await update.message.reply_text(text, parse_mode='Markdown')

@admin_required()
@log_activity('view_logs')
async def logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = next(get_db())
    
    # Get last 20 logs
    logs = db.query(AdminLog).order_by(AdminLog.timestamp.desc()).limit(20).all()
    
    text = "📋 *Activity Logs (Last 20)*\n\n"
    
    if logs:
        for log in logs:
            time_str = log.timestamp.strftime('%d/%m %H:%M')
            text += f"• [{time_str}] `{log.admin_id}`: {log.action}\n"
            if log.details:
                text += f"  _{log.details[:50]}..._\n"
    else:
        text += "Belum ada logs."
    
    keyboard = [[InlineKeyboardButton("🔄 Refresh", callback_data="logs_refresh")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)

async def handle_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle broadcast message input"""
    if 'broadcast_step' not in context.user_data:
        return
    
    if context.user_data['broadcast_step'] == 'waiting_message':
        # Save message
        context.user_data['broadcast_message'] = update.message.text
        context.user_data['broadcast_step'] = 'waiting_confirmation'
        
        # Show preview and options
        text = f"""📨 *Preview Broadcast*

{update.message.text}

*Options:*
• /confirm - Kirim broadcast sekarang
• /schedule - Jadwalkan broadcast
• /cancel - Batalkan

Pilih opsi di atas."""
        
        await update.message.reply_text(text, parse_mode='Markdown')

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith('users_page_'):
        page = data
