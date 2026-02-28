"""
TELEGRAM BOT SUPER LENGKAP - BOLAPELANGI 2
VERSI: ULTIMATE PRO v3.0
Fitur: Auto Welcome | Auto Post Scheduler | Broadcast | Admin Panel | User Tracking | Full Config via Telegram
Created for: @bolapelangi2_bot
Author: Sistem Profesional
"""
import threading
import os
try:
    from flask import Flask, jsonify
    WEB_SERVER_AVAILABLE = True
except ImportError:
    WEB_SERVER_AVAILABLE = False
    print("⚠️ Flask tidak terinstall. Health check Railway mungkin gagal.")

if WEB_SERVER_AVAILABLE:
    app = Flask(__name__)
    
    @app.route('/')
    @app.route('/health')
    def health_check():
        return jsonify({"status": "ok", "message": "Bot is running"})
    
    def run_web_server():
        port = int(os.environ.get("PORT", 8080))
        app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
    
    # Jalankan web server di thread terpisah
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    print(f"🌐 Web server started on port {os.environ.get('PORT', 8080)} for Railway health check")


import logging
import sys
import asyncio
import json
import sqlite3
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from pathlib import Path
from contextlib import contextmanager
from enum import Enum
import hashlib
import hmac
import base64
import re

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode

# ==================== LOAD ENVIRONMENT VARIABLES ====================

try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded .env file")
except ImportError:
    print("⚠️ python-dotenv not installed, using environment variables only")

print("=" * 80)
print("🔍 MEMULAI BOT BOLAPELANGI 2 ULTIMATE PRO v3.0...")
print("=" * 80)

# ==================== CONFIGURATION CLASS ====================

class BotConfig:
    """Centralized configuration management"""
    
    _instance = None
    _config = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.load_config()
    
    def load_config(self):
        """Load configuration from JSON files and environment"""
        # Default configuration
        self._config = {
            'bot': {
                'name': 'BOLAPELANGI 2 Bot',
                'version': '3.0.0',
                'environment': os.getenv('ENVIRONMENT', 'production'),
                'maintenance_mode': False
            },
            'super_admins': [850434834, 8122523608],
            'database': {
                'file': os.getenv('DATABASE_FILE', 'bot_database.db'),
                'backup_enabled': True,
                'backup_folder': 'backups',
                'auto_backup_interval': 24  # hours
            },
            'features': {
                'welcome_enabled': True,
                'auto_post_enabled': True,
                'broadcast_enabled': True,
                'user_tracking': True,
                'statistics': True,
                'admin_logs': True
            },
            'broadcast': {
                'delay_between_messages': 1,
                'max_per_day': 5,
                'max_length': 4096,
                'allow_scheduled': True
            },
            'urls': {
                'login': 'https://bopel2.link/login',
                'daftar': 'https://bopel2.link/daftar',
                'claim': 'https://bopel2.link/wa',
                'bot_official': 'https://t.me/bolapelangi2_bot',
                'prediksi': 'https://bopel2.vip/ChannelWA-Jadwal-Prediksi',
                'channel_wa': 'https://bopel2.vip/Channel-Whatsapp',
                'channel_tg': 'https://bopel2.vip/Channel-Telegram'
            },
            'images': {
                'default_promo': 'https://i.ibb.co/your-image/promo-banner.jpg',
                'default_welcome': 'https://i.ibb.co/your-image/welcome-banner.jpg'
            },
            'limits': {
                'users_per_page': 10,
                'max_posts': 50,
                'max_admins': 20,
                'max_broadcasts_history': 50
            },
            'messages': {
                'welcome': '👋 Halo {first_name}! Selamat datang di {bot_name}',
                'help': '📚 Gunakan /start untuk memulai',
                'error': '❌ Terjadi kesalahan. Silakan coba lagi.',
                'unauthorized': '❌ Anda tidak memiliki akses ke fitur ini.',
                'maintenance': '🔧 Bot sedang maintenance. Silakan coba nanti.'
            },
            'security': {
                'max_login_attempts': 5,
                'session_timeout': 3600,
                'require_auth_for_admin': True
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/bot_activity.log',
                'max_size_mb': 10,
                'backup_count': 5
            }
        }
        
        # Load from config.json if exists
        config_path = os.path.join('data', 'config.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    file_config = json.load(f)
                    self._deep_update(self._config, file_config)
                print(f"✅ Loaded config from {config_path}")
            except Exception as e:
                print(f"⚠️ Gagal load config.json: {e}")
        
        # Override with environment variables
        if os.getenv('BOT_TOKEN'):
            self._config['bot']['token'] = os.getenv('BOT_TOKEN')
        if os.getenv('CHANNEL_ID'):
            self._config['bot']['channel_id'] = int(os.getenv('CHANNEL_ID'))
        if os.getenv('DATABASE_FILE'):
            self._config['database']['file'] = os.getenv('DATABASE_FILE')
    
    def _deep_update(self, target, source):
        """Deep update dictionary"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value
    
    def get(self, key: str, default=None):
        """Get config value by dot notation"""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value
    
    def set(self, key: str, value: Any):
        """Set config value by dot notation"""
        keys = key.split('.')
        target = self._config
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        target[keys[-1]] = value
        
        # Auto save to file
        self.save()
    
    def save(self):
        """Save config to file"""
        try:
            os.makedirs('data', exist_ok=True)
            config_path = os.path.join('data', 'config.json')
            with open(config_path, 'w') as f:
                json.dump(self._config, f, indent=4)
            return True
        except Exception as e:
            logging.error(f"❌ Gagal save config: {e}")
            return False
    
    @property
    def token(self):
        return self.get('bot.token')
    
    @property
    def channel_id(self):
        return self.get('bot.channel_id', -1003573191693)
    
    @property
    def super_admins(self):
        return self.get('super_admins', [])

# Initialize config
config = BotConfig()

# ==================== CONSTANTS ====================

BOT_TOKEN = config.token
CHANNEL_ID = config.channel_id
SUPER_ADMINS = config.super_admins
DATABASE_FILE = config.get('database.file', 'bot_database.db')

print(f"🔍 BOT_TOKEN: {'ADA' if BOT_TOKEN else 'TIDAK ADA'}")
print(f"🔍 CHANNEL_ID: {CHANNEL_ID}")
print(f"🔍 DATABASE: {DATABASE_FILE}")
print(f"✅ SUPER ADMIN: {SUPER_ADMINS}")

# ==================== LOGGING CONFIGURATION ====================

os.makedirs('logs', exist_ok=True)
os.makedirs('data', exist_ok=True)
os.makedirs('backups', exist_ok=True)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, config.get('logging.level', 'INFO')),
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(config.get('logging.file', 'logs/bot_activity.log'), encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# ==================== ENUMS ====================

class UserRole(Enum):
    USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class BroadcastStatus(Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
    CANCELLED = "cancelled"
    FAILED = "failed"

class PostStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"

# ==================== TEKS PROMO ====================

PROMO_TEXT = """
⚽ *PROMO GILA! CASHBACK 100% MIX PARLAY* ⚽
*Satu Tim Meleset? Modal Kami Balikin Utuh!*

📋 *SYARAT:*
• Bet: Min Rp 10.000
• Tim: Min 5 tim (TODAY)
• Odds: Min 1.80/tim
• Provider: Sport 1/2

💡 *ATURAN:*
• 1 tim Lose Full
• Sisanya Win Full
• Max Rp 300.000/hari

⚠️ *WAJIB FOLLOW:*
🤖 [BOT OFFICIAL]({bot_official})
📈 [PREDIKSI JITU]({prediksi})
📢 [CHANNEL WHATSAPP]({channel_wa})
📢 [CHANNEL TELEGRAM]({channel_tg})
🟢 [KLAIM BONUS]({claim})

📌 *Catatan:* 1x/hari, no IP sama, no safety bet
🚀 *GASPOLL TERUS BOSKU!
""".format(
    bot_official=config.get('urls.bot_official'),
    prediksi=config.get('urls.prediksi'),
    channel_wa=config.get('urls.channel_wa'),
    channel_tg=config.get('urls.channel_tg'),
    claim=config.get('urls.claim')
)

# ==================== DATABASE MANAGER (ENHANCED) ====================

class DatabaseManager:
    """Enhanced database manager with migrations and backup"""
    
    VERSION = 3
    
    def __init__(self, db_file: str = DATABASE_FILE):
        self.db_file = db_file
        self._init_database()
        self._run_migrations()
        logger.info("✅ Enhanced Database Manager initialized")
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connection"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Database error: {e}")
            raise
        finally:
            conn.close()
    
    def _init_database(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Version table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS db_version (
                    version INTEGER PRIMARY KEY,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    language_code TEXT,
                    is_bot BOOLEAN,
                    joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_interactions INTEGER DEFAULT 0,
                    is_blocked BOOLEAN DEFAULT 0,
                    is_banned BOOLEAN DEFAULT 0,
                    ban_reason TEXT,
                    notes TEXT,
                    role TEXT DEFAULT 'user',
                    last_command TEXT,
                    last_message TEXT
                )
            ''')
            
            # Admins table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admins (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    added_by INTEGER,
                    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    permissions TEXT DEFAULT 'all',
                    role TEXT DEFAULT 'admin',
                    can_manage_users BOOLEAN DEFAULT 1,
                    can_manage_posts BOOLEAN DEFAULT 1,
                    can_broadcast BOOLEAN DEFAULT 1,
                    can_manage_admins BOOLEAN DEFAULT 0,
                    can_view_stats BOOLEAN DEFAULT 1,
                    can_edit_settings BOOLEAN DEFAULT 0,
                    FOREIGN KEY (added_by) REFERENCES users(user_id)
                )
            ''')
            
            # Auto posts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS auto_posts (
                    post_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    time TEXT NOT NULL,
                    text TEXT NOT NULL,
                    image_url TEXT,
                    button_text TEXT,
                    button_url TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_edited_by INTEGER,
                    last_edited_at TIMESTAMP,
                    schedule_days TEXT DEFAULT 'all',
                    priority INTEGER DEFAULT 0,
                    category TEXT DEFAULT 'general',
                    FOREIGN KEY (created_by) REFERENCES users(user_id)
                )
            ''')
            
            # Broadcast messages table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS broadcast_messages (
                    broadcast_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_text TEXT,
                    message_type TEXT,
                    file_id TEXT,
                    caption TEXT,
                    buttons TEXT,
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    scheduled_time TIMESTAMP,
                    sent_time TIMESTAMP,
                    status TEXT DEFAULT 'draft',
                    total_recipients INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    failed_count INTEGER DEFAULT 0,
                    filter_criteria TEXT,
                    is_template BOOLEAN DEFAULT 0,
                    template_name TEXT,
                    FOREIGN KEY (created_by) REFERENCES users(user_id)
                )
            ''')
            
            # Broadcast recipients table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS broadcast_recipients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    broadcast_id INTEGER,
                    user_id INTEGER,
                    sent_status TEXT DEFAULT 'pending',
                    sent_time TIMESTAMP,
                    error_message TEXT,
                    retry_count INTEGER DEFAULT 0,
                    FOREIGN KEY (broadcast_id) REFERENCES broadcast_messages(broadcast_id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # User interactions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    command TEXT,
                    message_text TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    response_time_ms INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # Settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    type TEXT DEFAULT 'string',
                    description TEXT,
                    updated_by INTEGER,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_public BOOLEAN DEFAULT 0
                )
            ''')
            
            # Logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_id INTEGER,
                    action TEXT,
                    target_type TEXT,
                    target_id TEXT,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    FOREIGN KEY (admin_id) REFERENCES admins(user_id)
                )
            ''')
            
            # Templates table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS templates (
                    template_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    type TEXT,
                    content TEXT,
                    variables TEXT,
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP,
                    use_count INTEGER DEFAULT 0
                )
            ''')
            
            # Insert super admins if not exist
            for admin_id in SUPER_ADMINS:
                cursor.execute('''
                    INSERT OR IGNORE INTO admins (user_id, role, can_manage_admins, can_edit_settings)
                    VALUES (?, 'super_admin', 1, 1)
                ''', (admin_id,))
            
            # Insert default settings
            default_settings = [
                ('welcome_enabled', str(config.get('features.welcome_enabled', True)).lower(), 'boolean', 'Enable welcome message'),
                ('auto_post_enabled', str(config.get('features.auto_post_enabled', True)).lower(), 'boolean', 'Enable auto posting'),
                ('broadcast_enabled', str(config.get('features.broadcast_enabled', True)).lower(), 'boolean', 'Enable broadcast feature'),
                ('broadcast_delay', str(config.get('broadcast.delay_between_messages', 1)), 'integer', 'Delay between broadcast messages (seconds)'),
                ('max_broadcast_per_day', str(config.get('broadcast.max_per_day', 5)), 'integer', 'Maximum broadcasts per day'),
                ('bot_name', config.get('bot.name', 'BOLAPELANGI 2 Bot'), 'string', 'Bot display name'),
                ('support_contact', '@admin', 'string', 'Support contact'),
                ('maintenance_mode', str(config.get('bot.maintenance_mode', False)).lower(), 'boolean', 'Maintenance mode'),
                ('max_broadcast_length', str(config.get('broadcast.max_length', 4096)), 'integer', 'Maximum broadcast message length'),
                ('users_per_page', str(config.get('limits.users_per_page', 10)), 'integer', 'Users per page in listing'),
            ]
            for key, value, typ, desc in default_settings:
                cursor.execute('INSERT OR IGNORE INTO settings (key, value, type, description) VALUES (?, ?, ?, ?)', 
                              (key, value, typ, desc))
            
            # Set version
            cursor.execute('INSERT OR IGNORE INTO db_version (version) VALUES (?)', (self.VERSION,))
    
    def _run_migrations(self):
        """Run database migrations"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT version FROM db_version ORDER BY version DESC LIMIT 1')
            row = cursor.fetchone()
            current_version = row['version'] if row else 0
            
            if current_version < self.VERSION:
                logger.info(f"🔄 Running migrations from v{current_version} to v{self.VERSION}")
                # Add migrations here as needed
                cursor.execute('UPDATE db_version SET version = ?', (self.VERSION,))
                logger.info("✅ Database migration completed")
    
    # ========== BACKUP & RESTORE ==========
    
    def backup_database(self) -> Optional[str]:
        """Create database backup"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = f"backups/backup_{timestamp}.db"
            
            with self.get_connection() as conn:
                backup_conn = sqlite3.connect(backup_file)
                conn.backup(backup_conn)
                backup_conn.close()
            
            logger.info(f"✅ Database backed up to {backup_file}")
            return backup_file
        except Exception as e:
            logger.error(f"❌ Backup failed: {e}")
            return None
    
    def restore_database(self, backup_file: str) -> bool:
        """Restore database from backup"""
        try:
            if not os.path.exists(backup_file):
                logger.error(f"❌ Backup file not found: {backup_file}")
                return False
            
            # Close all connections
            with self.get_connection() as conn:
                pass  # Just to ensure connection works
            
            # Restore
            backup_conn = sqlite3.connect(backup_file)
            with self.get_connection() as conn:
                backup_conn.backup(conn)
            backup_conn.close()
            
            logger.info(f"✅ Database restored from {backup_file}")
            return True
        except Exception as e:
            logger.error(f"❌ Restore failed: {e}")
            return False
    
    # ========== USER MANAGEMENT (ENHANCED) ==========
    
    def add_or_update_user(self, user: Any) -> bool:
        """Enhanced user tracking"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO users (
                        user_id, username, first_name, last_name, 
                        language_code, is_bot, last_active, total_interactions
                    ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 1)
                    ON CONFLICT(user_id) DO UPDATE SET
                        username = COALESCE(excluded.username, username),
                        first_name = COALESCE(excluded.first_name, first_name),
                        last_name = COALESCE(excluded.last_name, last_name),
                        language_code = COALESCE(excluded.language_code, language_code),
                        last_active = CURRENT_TIMESTAMP,
                        total_interactions = total_interactions + 1
                ''', (
                    user.id,
                    user.username,
                    user.first_name,
                    user.last_name,
                    user.language_code,
                    user.is_bot
                ))
                return True
        except Exception as e:
            logger.error(f"❌ Failed to update user {user.id}: {e}")
            return False
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_users(self, include_blocked: bool = False, limit: int = 1000, offset: int = 0) -> List[Dict]:
        """Get all users with pagination"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if include_blocked:
                cursor.execute('SELECT * FROM users ORDER BY joined_date DESC LIMIT ? OFFSET ?', (limit, offset))
            else:
                cursor.execute('SELECT * FROM users WHERE is_blocked = 0 ORDER BY joined_date DESC LIMIT ? OFFSET ?', (limit, offset))
            return [dict(row) for row in cursor.fetchall()]
    
    def search_users(self, query: str) -> List[Dict]:
        """Search users by username or name"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM users 
                WHERE username LIKE ? OR first_name LIKE ? OR last_name LIKE ?
                ORDER BY joined_date DESC LIMIT 50
            ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_user_stats(self) -> Dict:
        """Get detailed user statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total users
            cursor.execute('SELECT COUNT(*) as total FROM users')
            total = cursor.fetchone()[0]
            
            # Today's new users
            cursor.execute('SELECT COUNT(*) as today FROM users WHERE date(joined_date) = date("now")')
            today = cursor.fetchone()[0]
            
            # This week's new users
            cursor.execute('SELECT COUNT(*) as week FROM users WHERE joined_date >= datetime("now", "-7 days")')
            week = cursor.fetchone()[0]
            
            # This month's new users
            cursor.execute('SELECT COUNT(*) as month FROM users WHERE joined_date >= datetime("now", "-30 days")')
            month = cursor.fetchone()[0]
            
            # Active users (last 24h)
            cursor.execute('SELECT COUNT(*) as active_24h FROM users WHERE last_active > datetime("now", "-1 day")')
            active_24h = cursor.fetchone()[0]
            
            # Active users (last 7 days)
            cursor.execute('SELECT COUNT(*) as active_week FROM users WHERE last_active > datetime("now", "-7 days")')
            active_week = cursor.fetchone()[0]
            
            # Blocked users
            cursor.execute('SELECT COUNT(*) as blocked FROM users WHERE is_blocked = 1')
            blocked = cursor.fetchone()[0]
            
            # Banned users
            cursor.execute('SELECT COUNT(*) as banned FROM users WHERE is_banned = 1')
            banned = cursor.fetchone()[0]
            
            # Users by language
            cursor.execute('''
                SELECT language_code, COUNT(*) as count 
                FROM users 
                WHERE language_code IS NOT NULL 
                GROUP BY language_code 
                ORDER BY count DESC 
                LIMIT 5
            ''')
            languages = [dict(row) for row in cursor.fetchall()]
            
            return {
                'total': total,
                'today': today,
                'week': week,
                'month': month,
                'active_24h': active_24h,
                'active_week': active_week,
                'blocked': blocked,
                'banned': banned,
                'languages': languages
            }
    
    def block_user(self, user_id: int, reason: str = None) -> bool:
        """Block a user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET is_blocked = 1, notes = ? WHERE user_id = ?', (reason, user_id))
            return cursor.rowcount > 0
    
    def unblock_user(self, user_id: int) -> bool:
        """Unblock a user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET is_blocked = 0 WHERE user_id = ?', (user_id,))
            return cursor.rowcount > 0
    
    def ban_user(self, user_id: int, reason: str) -> bool:
        """Ban a user (stronger than block)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET is_banned = 1, ban_reason = ?, is_blocked = 1 WHERE user_id = ?', (reason, user_id))
            return cursor.rowcount > 0
    
    # ========== ADMIN MANAGEMENT (ENHANCED) ==========
    
    def get_user_role(self, user_id: int) -> UserRole:
        """Get user role"""
        if user_id in SUPER_ADMINS:
            return UserRole.SUPER_ADMIN
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT role FROM admins WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            if row:
                return UserRole.ADMIN if row['role'] == 'admin' else UserRole.SUPER_ADMIN
        return UserRole.USER
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        if user_id in SUPER_ADMINS:
            return True
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM admins WHERE user_id = ?', (user_id,))
            return cursor.fetchone() is not None
    
    def is_super_admin(self, user_id: int) -> bool:
        """Check if user is super admin"""
        if user_id in SUPER_ADMINS:
            return True
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT role FROM admins WHERE user_id = ? AND role = "super_admin"', (user_id,))
            return cursor.fetchone() is not None
    
    def add_admin(self, user_id: int, added_by: int, permissions: Dict = None) -> bool:
        """Add new admin with granular permissions"""
        try:
            if not self.is_super_admin(added_by):
                return False
            
            # Get username
            user_data = self.get_user(user_id)
            username = user_data['username'] if user_data else None
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Default permissions
                perms = {
                    'can_manage_users': True,
                    'can_manage_posts': True,
                    'can_broadcast': True,
                    'can_manage_admins': False,
                    'can_view_stats': True,
                    'can_edit_settings': False
                }
                if permissions:
                    perms.update(permissions)
                
                cursor.execute('''
                    INSERT OR REPLACE INTO admins (
                        user_id, username, added_by, role,
                        can_manage_users, can_manage_posts, can_broadcast,
                        can_manage_admins, can_view_stats, can_edit_settings
                    ) VALUES (?, ?, ?, 'admin', ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id, username, added_by,
                    perms['can_manage_users'], perms['can_manage_posts'], perms['can_broadcast'],
                    perms['can_manage_admins'], perms['can_view_stats'], perms['can_edit_settings']
                ))
                
                # Log action
                self.log_admin_action(added_by, 'add_admin', 'user', str(user_id), f"Added as admin with perms: {perms}")
                
                return True
        except Exception as e:
            logger.error(f"❌ Failed to add admin {user_id}: {e}")
            return False
    
    def remove_admin(self, user_id: int, removed_by: int) -> bool:
        """Remove admin"""
        try:
            if not self.is_super_admin(removed_by):
                return False
            
            if user_id in SUPER_ADMINS:
                return False
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM admins WHERE user_id = ?', (user_id,))
                
                # Log action
                self.log_admin_action(removed_by, 'remove_admin', 'user', str(user_id), "Removed admin")
                
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"❌ Failed to remove admin {user_id}: {e}")
            return False
    
    def update_admin_permissions(self, user_id: int, updated_by: int, permissions: Dict) -> bool:
        """Update admin permissions"""
        try:
            if not self.is_super_admin(updated_by):
                return False
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build SET clause dynamically
                set_clause = ', '.join([f"{key} = ?" for key in permissions.keys()])
                values = list(permissions.values()) + [user_id]
                
                cursor.execute(f'UPDATE admins SET {set_clause} WHERE user_id = ?', values)
                
                # Log action
                self.log_admin_action(updated_by, 'update_admin_permissions', 'user', str(user_id), f"Updated permissions: {permissions}")
                
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"❌ Failed to update admin permissions: {e}")
            return False
    
    def get_all_admins(self) -> List[Dict]:
        """Get all admins with details"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT a.*, u.first_name, u.username, u.last_active
                FROM admins a
                LEFT JOIN users u ON a.user_id = u.user_id
                ORDER BY 
                    CASE WHEN a.role = 'super_admin' THEN 0 ELSE 1 END,
                    a.added_date DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_admin_permissions(self, user_id: int) -> Dict:
        """Get admin permissions"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT can_manage_users, can_manage_posts, can_broadcast,
                       can_manage_admins, can_view_stats, can_edit_settings
                FROM admins WHERE user_id = ?
            ''', (user_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return {}
    
    # ========== ADMIN LOGS ==========
    
    def log_admin_action(self, admin_id: int, action: str, target_type: str, target_id: str, details: str = None):
        """Log admin actions"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO admin_logs (admin_id, action, target_type, target_id, details)
                    VALUES (?, ?, ?, ?, ?)
                ''', (admin_id, action, target_type, target_id, details))
        except Exception as e:
            logger.error(f"❌ Failed to log admin action: {e}")
    
    def get_admin_logs(self, limit: int = 100) -> List[Dict]:
        """Get admin action logs"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT l.*, u.username, u.first_name
                FROM admin_logs l
                LEFT JOIN users u ON l.admin_id = u.user_id
                ORDER BY l.timestamp DESC
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    # ========== BROADCAST MANAGEMENT (ENHANCED) ==========
    
    def create_broadcast(self, created_by: int, message_text: str, message_type: str = 'text', 
                         file_id: str = None, caption: str = None, buttons: Dict = None,
                         is_template: bool = False, template_name: str = None) -> int:
        """Create broadcast with template support"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO broadcast_messages (
                        message_text, message_type, file_id, caption, buttons, 
                        created_by, status, is_template, template_name
                    ) VALUES (?, ?, ?, ?, ?, ?, 'draft', ?, ?)
                ''', (
                    message_text, message_type, file_id, caption, 
                    json.dumps(buttons) if buttons else None, created_by,
                    is_template, template_name
                ))
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"❌ Failed to create broadcast: {e}")
            return -1
    
    def schedule_broadcast(self, broadcast_id: int, schedule_time: datetime, filter_criteria: Dict = None) -> bool:
        """Schedule broadcast with filters"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE broadcast_messages 
                    SET scheduled_time = ?, status = 'scheduled', filter_criteria = ?
                    WHERE broadcast_id = ?
                ''', (schedule_time.isoformat(), json.dumps(filter_criteria) if filter_criteria else None, broadcast_id))
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"❌ Failed to schedule broadcast: {e}")
            return False
    
    def get_pending_broadcasts(self) -> List[Dict]:
        """Get pending scheduled broadcasts"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM broadcast_messages 
                WHERE status = 'scheduled' 
                AND scheduled_time <= datetime('now')
                ORDER BY scheduled_time
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_broadcasts(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get all broadcasts with pagination"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT b.*, u.username as creator_username, u.first_name as creator_name
                FROM broadcast_messages b
                LEFT JOIN users u ON b.created_by = u.user_id
                ORDER BY b.created_at DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_broadcast_stats(self) -> Dict:
        """Get broadcast statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM broadcast_messages')
            total = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM broadcast_messages WHERE status = "sent"')
            sent = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM broadcast_messages WHERE status = "scheduled"')
            scheduled = cursor.fetchone()[0]
            
            cursor.execute('SELECT SUM(success_count) FROM broadcast_messages')
            total_success = cursor.fetchone()[0] or 0
            
            cursor.execute('SELECT SUM(failed_count) FROM broadcast_messages')
            total_failed = cursor.fetchone()[0] or 0
            
            return {
                'total': total,
                'sent': sent,
                'scheduled': scheduled,
                'total_success': total_success,
                'total_failed': total_failed,
                'success_rate': (total_success / (total_success + total_failed) * 100) if (total_success + total_failed) > 0 else 0
            }
    
    # ========== TEMPLATES ==========
    
    def create_template(self, name: str, template_type: str, content: str, 
                        variables: List[str] = None, created_by: int = None) -> int:
        """Create message template"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO templates (name, type, content, variables, created_by)
                    VALUES (?, ?, ?, ?, ?)
                ''', (name, template_type, content, json.dumps(variables) if variables else None, created_by))
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"❌ Failed to create template: {e}")
            return -1
    
    def get_templates(self, template_type: str = None) -> List[Dict]:
        """Get all templates"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if template_type:
                cursor.execute('SELECT * FROM templates WHERE type = ? ORDER BY name', (template_type,))
            else:
                cursor.execute('SELECT * FROM templates ORDER BY name')
            return [dict(row) for row in cursor.fetchall()]
    
    def render_template(self, template_id: int, variables: Dict) -> Optional[str]:
        """Render template with variables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT content, variables FROM templates WHERE template_id = ?', (template_id,))
            row = cursor.fetchone()
            if not row:
                return None
            
            content = row['content']
            template_vars = json.loads(row['variables']) if row['variables'] else []
            
            # Replace variables
            for var in template_vars:
                if var in variables:
                    content = content.replace(f'{{{var}}}', str(variables[var]))
            
            # Update usage stats
            cursor.execute('UPDATE templates SET last_used = CURRENT_TIMESTAMP, use_count = use_count + 1 WHERE template_id = ?', (template_id,))
            
            return content
    
    # ========== AUTO POST MANAGEMENT ==========
    
    def get_all_posts(self, include_inactive: bool = False) -> List[Dict]:
        """Get all auto posts"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if include_inactive:
                cursor.execute('SELECT * FROM auto_posts ORDER BY time')
            else:
                cursor.execute('SELECT * FROM auto_posts WHERE is_active = 1 ORDER BY time')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_post(self, post_id: int) -> Optional[Dict]:
        """Get single post"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM auto_posts WHERE post_id = ?', (post_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def add_post(self, time_str: str, text: str, image_url: str = None, 
                 button_text: str = None, button_url: str = None, 
                 created_by: int = None, category: str = 'general',
                 priority: int = 0) -> int:
        """Add new auto post"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO auto_posts (time, text, image_url, button_text, button_url, created_by, category, priority)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (time_str, text, image_url, button_text, button_url, created_by, category, priority))
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"❌ Failed to add post: {e}")
            return -1
    
    def update_post(self, post_id: int, **kwargs) -> bool:
        """Update auto post"""
        try:
            fields = []
            values = []
            for key, value in kwargs.items():
                if value is not None:
                    fields.append(f"{key} = ?")
                    values.append(value)
            
            if not fields:
                return False
            
            values.append(post_id)
            query = f"UPDATE auto_posts SET {', '.join(fields)} WHERE post_id = ?"
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, values)
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"❌ Failed to update post {post_id}: {e}")
            return False
    
    def delete_post(self, post_id: int) -> bool:
        """Delete auto post"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM auto_posts WHERE post_id = ?', (post_id,))
            return cursor.rowcount > 0
    
    def toggle_post(self, post_id: int) -> bool:
        """Toggle post active status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE auto_posts SET is_active = NOT is_active WHERE post_id = ?', (post_id,))
            return cursor.rowcount > 0
    
    def get_posts_by_category(self, category: str) -> List[Dict]:
        """Get posts by category"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM auto_posts WHERE category = ? AND is_active = 1 ORDER BY priority DESC, time', (category,))
            return [dict(row) for row in cursor.fetchall()]
    
    # ========== SETTINGS MANAGEMENT ==========
    
    def get_setting(self, key: str, default: str = None) -> str:
        """Get setting value"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
            row = cursor.fetchone()
            return row['value'] if row else default
    
    def get_setting_with_type(self, key: str, default=None) -> Any:
        """Get setting with proper type conversion"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value, type FROM settings WHERE key = ?', (key,))
            row = cursor.fetchone()
            if not row:
                return default
            
            value = row['value']
            typ = row['type']
            
            if typ == 'boolean':
                return value.lower() == 'true'
            elif typ == 'integer':
                try:
                    return int(value)
                except:
                    return default
            elif typ == 'float':
                try:
                    return float(value)
                except:
                    return default
            elif typ == 'json':
                try:
                    return json.loads(value)
                except:
                    return default
            else:
                return value
    
    def update_setting(self, key: str, value: str, updated_by: int, value_type: str = None) -> bool:
        """Update setting"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if value_type:
                    cursor.execute('''
                        UPDATE settings SET value = ?, updated_by = ?, updated_at = CURRENT_TIMESTAMP, type = ?
                        WHERE key = ?
                    ''', (value, updated_by, value_type, key))
                else:
                    cursor.execute('''
                        UPDATE settings SET value = ?, updated_by = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE key = ?
                    ''', (value, updated_by, key))
                
                if cursor.rowcount > 0:
                    # Update config cache
                    config.set(key, value)
                    return True
                return False
        except Exception as e:
            logger.error(f"❌ Failed to update setting {key}: {e}")
            return False
    
    def get_all_settings(self, public_only: bool = False) -> List[Dict]:
        """Get all settings"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if public_only:
                cursor.execute('SELECT * FROM settings WHERE is_public = 1 ORDER BY key')
            else:
                cursor.execute('SELECT * FROM settings ORDER BY key')
            return [dict(row) for row in cursor.fetchall()]
    
    # ========== INTERACTION LOGGING ==========
    
    def log_interaction(self, user_id: int, command: str, message_text: str = None, response_time: int = None):
        """Log user interaction"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO user_interactions (user_id, command, message_text, response_time_ms)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, command, message_text, response_time))
        except Exception as e:
            logger.error(f"❌ Failed to log interaction: {e}")

# Initialize database
db = DatabaseManager()

# ==================== LOAD JSON DATA ====================

def load_initial_data():
    """Load initial data from JSON files"""
    try:
        data_folder = 'data'
        
        # Load auto_posts.json
        posts_path = os.path.join(data_folder, 'auto_posts.json')
        if os.path.exists(posts_path):
            with open(posts_path, 'r') as f:
                posts = json.load(f)
            
            # Check if empty
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM auto_posts')
                count = cursor.fetchone()[0]
                
                if count == 0 and posts:
                    for post in posts:
                        db.add_post(
                            time_str=post.get('time'),
                            text=post.get('text'),
                            image_url=post.get('image_url'),
                            button_text=post.get('button_text'),
                            button_url=post.get('button_url'),
                            created_by=SUPER_ADMINS[0] if SUPER_ADMINS else 850434834,
                            category=post.get('category', 'general')
                        )
                    logger.info(f"✅ Loaded {len(posts)} auto posts")
        
        # Load templates
        templates_path = os.path.join(data_folder, 'broadcast_templates.json')
        if os.path.exists(templates_path):
            with open(templates_path, 'r') as f:
                templates = json.load(f)
            
            for template in templates:
                db.create_template(
                    name=template['name'],
                    template_type=template.get('type', 'text'),
                    content=template['text'],
                    variables=['first_name', 'user_id', 'username'],
                    created_by=SUPER_ADMINS[0] if SUPER_ADMINS else 850434834
                )
            logger.info(f"✅ Loaded {len(templates)} templates")
        
        # Load settings from bot_settings.json
        settings_path = os.path.join(data_folder, 'bot_settings.json')
        if os.path.exists(settings_path):
            with open(settings_path, 'r') as f:
                settings = json.load(f)
            
            if 'limits' in settings:
                for key, value in settings['limits'].items():
                    db.update_setting(key, str(value), SUPER_ADMINS[0] if SUPER_ADMINS else 850434834)
            
            if 'messages' in settings:
                for key, value in settings['messages'].items():
                    db.update_setting(f'message_{key}', value, SUPER_ADMINS[0] if SUPER_ADMINS else 850434834)
            
            logger.info(f"✅ Loaded settings")
            
    except Exception as e:
        logger.error(f"❌ Failed to load initial data: {e}")

# Load initial data
load_initial_data()

# ==================== AUTO POST SCHEDULER ====================

class AutoPostScheduler:
    """Enhanced auto post scheduler"""
    
    def __init__(self):
        self.running = True
        self.last_check = None
        logger.info("✅ AutoPostScheduler initialized")
    
    async def check_and_send_posts(self, context: ContextTypes.DEFAULT_TYPE):
        """Check and send scheduled posts"""
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        current_day = now.strftime("%a").lower()
        
        # Check if auto post is enabled
        if not db.get_setting_with_type('auto_post_enabled', True):
            return
        
        # Get all active posts
        posts = db.get_all_posts(include_inactive=False)
        
        for post in posts:
            # Check time
            if post['time'] != current_time:
                continue
            
            # Check schedule days
            schedule_days = post.get('schedule_days', 'all')
            if schedule_days != 'all' and current_day not in schedule_days.split(','):
                continue
            
            await self.send_post(context, post)
    
    async def send_post(self, context: ContextTypes.DEFAULT_TYPE, post: Dict):
        """Send post to channel"""
        try:
            logger.info(f"📢 Sending auto post ID {post['post_id']} - {post['time']}")
            
            # Create keyboard if has button
            reply_markup = None
            if post.get('button_text') and post.get('button_url'):
                keyboard = [[InlineKeyboardButton(post['button_text'], url=post['button_url'])]]
                reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send with image if available
            if post.get('image_url'):
                try:
                    await context.bot.send_photo(
                        chat_id=CHANNEL_ID,
                        photo=post['image_url'],
                        caption=post['text'],
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=reply_markup
                    )
                    logger.info(f"✅ Auto post {post['post_id']} sent with image")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to send image: {e}, sending text only")
                    await context.bot.send_message(
                        chat_id=CHANNEL_ID,
                        text=post['text'],
                        parse_mode=ParseMode.MARKDOWN,
                        disable_web_page_preview=True,
                        reply_markup=reply_markup
                    )
            else:
                await context.bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=post['text'],
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True,
                    reply_markup=reply_markup
                )
                logger.info(f"✅ Auto post {post['post_id']} sent")
            
            # Update last sent
            db.update_post(post['post_id'], last_edited_at=datetime.now().isoformat())
            
        except Exception as e:
            logger.error(f"❌ Failed to send auto post {post['post_id']}: {e}")

scheduler = AutoPostScheduler()

# ==================== BROADCAST MANAGER (ENHANCED) ====================

class BroadcastManager:
    """Enhanced broadcast manager with queue and filters"""
    
    def __init__(self):
        self.current_broadcast = None
        self.broadcast_queue = asyncio.Queue()
        self.is_sending = False
        logger.info("✅ Enhanced BroadcastManager initialized")
    
    async def send_broadcast(self, context: ContextTypes.DEFAULT_TYPE, 
                            broadcast_id: int, message_text: str, 
                            message_type: str = 'text', file_id: str = None,
                            caption: str = None, buttons: Dict = None,
                            filter_criteria: Dict = None):
        """Send broadcast with filters"""
        
        # Get filtered users
        users = self._filter_users(filter_criteria) if filter_criteria else db.get_all_users()
        total_users = len(users)
        
        if total_users == 0:
            logger.warning("⚠️ No users to broadcast")
            return
        
        # Update broadcast
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE broadcast_messages 
                SET total_recipients = ?, status = 'sending' 
                WHERE broadcast_id = ?
            ''', (total_users, broadcast_id))
        
        # Create keyboard
        reply_markup = None
        if buttons:
            keyboard = []
            for btn in buttons.get('inline_keyboard', []):
                row = []
                for button in btn:
                    row.append(InlineKeyboardButton(
                        button['text'], 
                        url=button.get('url'),
                        callback_data=button.get('callback_data')
                    ))
                keyboard.append(row)
            if keyboard:
                reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send to users
        success = 0
        failed = 0
        delay = db.get_setting_with_type('broadcast_delay', 1)
        
        self.is_sending = True
        self.current_broadcast = broadcast_id
        
        for user in users:
            user_id = user['user_id']
            
            # Skip blocked/banned
            if user.get('is_blocked') or user.get('is_banned'):
                continue
            
            try:
                if message_type == 'text':
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=message_text,
                        parse_mode=ParseMode.MARKDOWN,
                        disable_web_page_preview=True,
                        reply_markup=reply_markup
                    )
                elif message_type == 'photo' and file_id:
                    await context.bot.send_photo(
                        chat_id=user_id,
                        photo=file_id,
                        caption=caption or message_text,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=reply_markup
                    )
                
                success += 1
                
                # Log success
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO broadcast_recipients (broadcast_id, user_id, sent_status, sent_time)
                        VALUES (?, ?, 'success', CURRENT_TIMESTAMP)
                    ''', (broadcast_id, user_id))
                
            except Exception as e:
                failed += 1
                logger.error(f"❌ Failed to send to {user_id}: {e}")
                
                # Log failure
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO broadcast_recipients (broadcast_id, user_id, sent_status, error_message)
                        VALUES (?, ?, 'failed', ?)
                    ''', (broadcast_id, user_id, str(e)[:200]))
            
            # Delay to avoid flood
            await asyncio.sleep(delay)
        
        # Update final status
        db.update_broadcast_status(broadcast_id, 'sent', success, failed)
        
        self.is_sending = False
        self.current_broadcast = None
        
        logger.info(f"✅ Broadcast {broadcast_id} completed: {success} success, {failed} failed")
        return {'success': success, 'failed': failed, 'total': total_users}
    
    def _filter_users(self, criteria: Dict) -> List[Dict]:
        """Filter users based on criteria"""
        if not criteria:
            return db.get_all_users()
        
        # Build SQL conditions
        conditions = ["1=1"]
        params = []
        
        if criteria.get('active_last_days'):
            conditions.append("last_active > datetime('now', '-? days')")
            params.append(criteria['active_last_days'])
        
        if criteria.get('language'):
            conditions.append("language_code = ?")
            params.append(criteria['language'])
        
        if criteria.get('joined_after'):
            conditions.append("joined_date > ?")
            params.append(criteria['joined_after'])
        
        if criteria.get('not_blocked'):
            conditions.append("is_blocked = 0")
        
        if criteria.get('not_banned'):
            conditions.append("is_banned = 0")
        
        query = f"SELECT * FROM users WHERE {' AND '.join(conditions)} ORDER BY joined_date DESC"
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    async def process_queue(self, context: ContextTypes.DEFAULT_TYPE):
        """Process broadcast queue"""
        while True:
            try:
                if not self.broadcast_queue.empty() and not self.is_sending:
                    broadcast_data = await self.broadcast_queue.get()
                    await self.send_broadcast(context, **broadcast_data)
            except Exception as e:
                logger.error(f"❌ Error processing broadcast queue: {e}")
            await asyncio.sleep(1)

broadcast_manager = BroadcastManager()

# ==================== DECORATORS ====================

def role_required(min_role: UserRole = UserRole.ADMIN):
    """Decorator for role-based access control"""
    def decorator(func):
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user = update.effective_user
            user_role = db.get_user_role(user.id)
            
            # Check maintenance mode
            if db.get_setting_with_type('maintenance_mode', False) and user_role != UserRole.SUPER_ADMIN:
                await update.message.reply_text(
                    config.get('messages.maintenance', '🔧 Bot sedang maintenance. Silakan coba nanti.'),
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            role_levels = {
                UserRole.USER: 0,
                UserRole.ADMIN: 1,
                UserRole.SUPER_ADMIN: 2
            }
            
            if role_levels.get(user_role, 0) < role_levels.get(min_role, 1):
                await update.message.reply_text(
                    config.get('messages.unauthorized', '❌ Anda tidak memiliki akses ke fitur ini.'),
                    parse_mode=ParseMode.MARKDOWN
                )
                logger.warning(f"⚠️ Unauthorized access attempt by user {user.id}")
                return
            
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator

# ==================== COMMAND HANDLERS ====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    start_time = datetime.now()
    
    # Save user
    db.add_or_update_user(user)
    
    # Check if blocked/banned
    user_data = db.get_user(user.id)
    if user_data and user_data.get('is_banned'):
        await update.message.reply_text(
            "❌ *Akses Diblokir Permanen*\n\nMaaf, akun Anda telah diblokir permanen oleh admin.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if user_data and user_data.get('is_blocked'):
        await update.message.reply_text(
            "❌ *Akses Diblokir Sementara*\n\nMaaf, akses Anda sedang diblokir oleh admin.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    logger.info(f"🚀 /start from {user.first_name} (ID: {user.id}, @{user.username})")
    
    # Personalized welcome
    welcome_templates = db.get_templates('welcome')
    if welcome_templates:
        welcome_text = db.render_template(
            welcome_templates[0]['template_id'],
            {
                'first_name': user.first_name,
                'user_id': user.id,
                'username': user.username or 'tidak ada',
                'bot_name': db.get_setting('bot_name')
            }
        )
    else:
        welcome_text = (
            f"👋 *Halo {user.first_name}!*\n\n"
            f"Selamat datang di *{db.get_setting('bot_name')}*\n\n"
            f"📌 *Layanan Kami:*\n"
            f"• Info Promo Terbaru\n"
            f"• Link Login & Daftar\n"
            f"• Klaim Event Bonus\n"
            f"• Update Prediksi Jitu\n\n"
            f"✨ *Menu Tersedia:*\n"
            f"• Klik tombol di bawah untuk akses cepat\n"
            f"• Ketik /help untuk bantuan\n"
            f"• Ketik /promo untuk lihat promo\n\n"
            f"🔥 *GasPoll!* 🔥"
        )
    
    # Build keyboard
    keyboard = [
        [
            InlineKeyboardButton("🔐 LOGIN", callback_data='login'),
            InlineKeyboardButton("📝 DAFTAR", callback_data='daftar'),
        ],
        [
            InlineKeyboardButton("🎁 CLAIM BONUS", callback_data='claim'),
        ],
        [
            InlineKeyboardButton("📢 LIHAT PROMO", callback_data='promo'),
        ]
    ]
    
    # Add admin button if admin
    if db.is_admin(user.id):
        keyboard.append([InlineKeyboardButton("⚙️ PANEL ADMIN", callback_data='admin_dashboard')])
    
    # Add super admin button
    if db.is_super_admin(user.id):
        keyboard.append([InlineKeyboardButton("⭐ SUPER ADMIN PANEL", callback_data='super_admin_dashboard')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        text=welcome_text,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
        reply_markup=reply_markup
    )
    
    # Log response time
    response_time = int((datetime.now() - start_time).total_seconds() * 1000)
    db.log_interaction(user.id, '/start', response_time=response_time)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    user = update.effective_user
    db.add_or_update_user(user)
    
    role = db.get_user_role(user.id)
    
    help_text = (
        "📚 *BANTUAN BOT*\n\n"
        "✨ *Perintah untuk Semua User:*\n"
        "• /start - Mulai bot\n"
        "• /promo - Lihat promo terbaru\n"
        "• /help - Tampilkan bantuan ini\n"
        "• /info - Info akun Anda\n"
        "• /stats - Statistik bot (public)\n"
    )
    
    if role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        help_text += (
            "\n👑 *Perintah Admin:*\n"
            "• /admin - Dashboard admin\n"
            "• /users - Daftar user\n"
            "• /broadcast - Kirim broadcast\n"
            "• /posts - Kelola auto post\n"
            "• /templates - Kelola template\n"
        )
    
    if role == UserRole.SUPER_ADMIN:
        help_text += (
            "\n⭐ *Perintah Super Admin:*\n"
            "• /admins - Kelola admin\n"
            "• /settings - Pengaturan bot\n"
            "• /backup - Backup database\n"
            "• /restore - Restore database\n"
            "• /logs - Lihat log aktivitas\n"
            "• /maintenance - Mode maintenance\n"
        )
    
    help_text += f"\n📞 *Kontak Support:*\n{db.get_setting('support_contact', '@admin')}"
    
    keyboard = [[InlineKeyboardButton("🔙 KEMBALI KE MENU", callback_data='back_to_menu')]]
    
    await update.message.reply_text(
        text=help_text,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    db.log_interaction(user.id, '/help')

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /info command"""
    user = update.effective_user
    db.add_or_update_user(user)
    
    user_data = db.get_user(user.id)
    role = db.get_user_role(user.id)
    
    # Get user stats
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM user_interactions WHERE user_id = ?', (user.id,))
        interactions = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM broadcast_recipients WHERE user_id = ? AND sent_status = "success"', (user.id,))
        broadcasts_received = cursor.fetchone()[0]
    
    role_emoji = {
        UserRole.USER: "👤",
        UserRole.ADMIN: "👑",
        UserRole.SUPER_ADMIN: "⭐"
    }
    
    role_text = {
        UserRole.USER: "USER BIASA",
        UserRole.ADMIN: "ADMIN",
        UserRole.SUPER_ADMIN: "SUPER ADMIN"
    }
    
    text = (
        f"👤 *INFO AKUN ANDA*\n\n"
        f"{role_emoji[role]} *User ID:* `{user.id}`\n"
        f"👤 *Nama:* {user.first_name} {user.last_name or ''}\n"
        f"📛 *Username:* @{user.username or 'tidak ada'}\n"
        f"🌍 *Bahasa:* {user.language_code or 'id'}\n"
        f"📅 *Bergabung:* {user_data['joined_date'] if user_data else 'Sekarang'}\n"
        f"🕐 *Terakhir Aktif:* {user_data['last_active'] if user_data else 'Sekarang'}\n"
        f"📊 *Total Interaksi:* {interactions}\n"
        f"📢 *Broadcast Diterima:* {broadcasts_received}\n"
        f"🔰 *Status:* {role_emoji[role]} *{role_text[role]}*\n"
    )
    
    if role == UserRole.ADMIN:
        perms = db.get_admin_permissions(user.id)
        text += f"\n🔑 *Izin Admin:*\n"
        text += f"• Manage Users: {'✅' if perms.get('can_manage_users') else '❌'}\n"
        text += f"• Manage Posts: {'✅' if perms.get('can_manage_posts') else '❌'}\n"
        text += f"• Broadcast: {'✅' if perms.get('can_broadcast') else '❌'}\n"
        text += f"• View Stats: {'✅' if perms.get('can_view_stats') else '❌'}\n"
    
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    db.log_interaction(user.id, '/info')

async def promo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /promo command"""
    user = update.effective_user
    db.add_or_update_user(user)
    
    logger.info(f"🎁 /promo from {user.first_name}")
    
    # Get promo image
    image_url = config.get('images.default_promo')
    posts = db.get_all_posts()
    for post in posts:
        if post.get('image_url'):
            image_url = post['image_url']
            break
    
    # Build keyboard
    keyboard = [
        [InlineKeyboardButton("🤖 BOT OFFICIAL", url=config.get('urls.bot_official'))],
        [InlineKeyboardButton("📈 PREDIKSI JITU", url=config.get('urls.prediksi'))],
        [InlineKeyboardButton("📢 CHANNEL WA", url=config.get('urls.channel_wa'))],
        [InlineKeyboardButton("📢 CHANNEL TG", url=config.get('urls.channel_tg'))],
        [InlineKeyboardButton("🟢 KLAIM BONUS", url=config.get('urls.claim'))],
        [InlineKeyboardButton("🔙 KEMBALI KE MENU", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await update.message.reply_photo(
            photo=image_url,
            caption=PROMO_TEXT,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        logger.info("✅ Promo sent with image")
    except Exception as e:
        logger.warning(f"⚠️ Failed to send image: {e}")
        await update.message.reply_text(
            text=PROMO_TEXT,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=reply_markup
        )
    
    db.log_interaction(user.id, '/promo')

# ==================== ADMIN DASHBOARD ====================

@role_required(UserRole.ADMIN)
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin command"""
    user = update.effective_user
    role = db.get_user_role(user.id)
    
    # Get stats
    user_stats = db.get_user_stats()
    posts = db.get_all_posts()
    active_posts = sum(1 for p in posts if p['is_active'])
    broadcast_stats = db.get_broadcast_stats()
    
    # Get pending tasks
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM broadcast_messages WHERE status = "scheduled"')
        scheduled_broadcasts = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM admin_logs WHERE date(timestamp) = date("now")')
        today_logs = cursor.fetchone()[0]
    
    text = (
        "⚙️ *DASHBOARD ADMIN*\n\n"
        f"👤 *Admin:* {user.first_name}\n"
        f"🆔 *ID:* `{user.id}`\n"
        f"👑 *Level:* {'⭐ SUPER ADMIN' if role == UserRole.SUPER_ADMIN else '👑 ADMIN'}\n\n"
        f"📊 *STATISTIK BOT*\n"
        f"• Total User: {user_stats['total']}\n"
        f"• User Baru Hari Ini: {user_stats['today']}\n"
        f"• User Aktif 24h: {user_stats['active_24h']}\n"
        f"• User Diblokir: {user_stats['blocked']}\n\n"
        f"📅 *AUTO POST*\n"
        f"• Total Jadwal: {len(posts)}\n"
        f"• Jadwal Aktif: {active_posts}\n\n"
        f"📢 *BROADCAST*\n"
        f"• Total Broadcast: {broadcast_stats['total']}\n"
        f"• Terjadwal: {scheduled_broadcasts}\n"
        f"• Success Rate: {broadcast_stats['success_rate']:.1f}%\n\n"
        f"📋 *AKTIVITAS*\n"
        f"• Log Hari Ini: {today_logs}\n"
    )
    
    # Build menu based on permissions
    keyboard = []
    
    perms = db.get_admin_permissions(user.id) if role == UserRole.ADMIN else {
        'can_manage_users': True,
        'can_manage_posts': True,
        'can_broadcast': True,
        'can_view_stats': True
    }
    
    if perms.get('can_manage_users'):
        keyboard.append([InlineKeyboardButton("👥 MANAJEMEN USER", callback_data='admin_users')])
    
    if perms.get('can_broadcast'):
        keyboard.append([InlineKeyboardButton("📢 BROADCAST", callback_data='admin_broadcast')])
    
    if perms.get('can_manage_posts'):
        keyboard.append([InlineKeyboardButton("📅 AUTO POST", callback_data='admin_posts')])
    
    if perms.get('can_view_stats'):
        keyboard.append([InlineKeyboardButton("📊 STATISTIK", callback_data='admin_stats')])
        keyboard.append([InlineKeyboardButton("📋 LOG AKTIVITAS", callback_data='admin_logs')])
    
    # Super admin only
    if role == UserRole.SUPER_ADMIN:
        keyboard.extend([
            [InlineKeyboardButton("👑 KELOLA ADMIN", callback_data='admin_manage_admins')],
            [InlineKeyboardButton("⚙️ PENGATURAN", callback_data='admin_settings')],
            [InlineKeyboardButton("💾 BACKUP & RESTORE", callback_data='admin_backup')],
            [InlineKeyboardButton("📝 TEMPLATE", callback_data='admin_templates')],
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 KEMBALI KE MENU", callback_data='back_to_menu')])
    
    await update.message.reply_text(
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    db.log_interaction(user.id, '/admin')
    db.log_admin_action(user.id, 'view_dashboard', 'system', 'admin', 'Viewed admin dashboard')

# ==================== USER MANAGEMENT COMMANDS ====================

@role_required(UserRole.ADMIN)
async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /users command"""
    user = update.effective_user
    perms = db.get_admin_permissions(user.id) if db.get_user_role(user.id) == UserRole.ADMIN else {'can_manage_users': True}
    
    if not perms.get('can_manage_users') and db.get_user_role(user.id) != UserRole.SUPER_ADMIN:
        await update.message.reply_text("❌ Anda tidak memiliki izin untuk mengelola user.")
        return
    
    # Parse arguments
    args = context.args
    page = 1
    search_query = None
    
    if args:
        if args[0].isdigit():
            page = int(args[0])
        else:
            search_query = ' '.join(args)
    
    if search_query:
        users = db.search_users(search_query)
        text = f"📋 *HASIL PENCARIAN: '{search_query}'*\n\n"
        if not users:
            text += "Tidak ada user ditemukan."
    else:
        per_page = db.get_setting_with_type('users_per_page', 10)
        offset = (page - 1) * per_page
        users = db.get_all_users(limit=per_page, offset=offset)
        total = db.get_user_count()['total']
        total_pages = (total + per_page - 1) // per_page
        
        text = f"📋 *DAFTAR USER (Halaman {page}/{total_pages})*\n\n"
        text += f"Total: {total} user\n\n"
    
    for u in users[:10]:  # Show max 10
        status = "⛔" if u.get('is_blocked') else "✅"
        banned = "🚫" if u.get('is_banned') else ""
        role = "👑" if db.is_admin(u['user_id']) else "👤"
        
        text += f"{status}{banned}{role} `{u['user_id']}` - {u['first_name']}"
        if u.get('username'):
            text += f" @{u['username']}"
        text += f"\n   📅 {u['joined_date'][:10]} | 🕐 {u['last_active'][:16]}\n"
    
    # Build navigation
    keyboard = []
    if not search_query and total_pages > 1:
        nav_row = []
        if page > 1:
            nav_row.append(InlineKeyboardButton("◀️", callback_data=f'users_page_{page-1}'))
        nav_row.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data='noop'))
        if page < total_pages:
            nav_row.append(InlineKeyboardButton("▶️", callback_data=f'users_page_{page+1}'))
        keyboard.append(nav_row)
    
    # Action buttons
    action_row = []
    if db.is_super_admin(user.id):
        action_row.append(InlineKeyboardButton("🔍 SEARCH", callback_data='user_search'))
        action_row.append(InlineKeyboardButton("⛔ BLOCK", callback_data='user_block'))
    keyboard.append(action_row)
    
    keyboard.append([InlineKeyboardButton("🔙 KEMBALI", callback_data='admin_dashboard')])
    
    await update.message.reply_text(
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    db.log_interaction(user.id, '/users')

# ==================== SUPER ADMIN COMMANDS ====================

@role_required(UserRole.SUPER_ADMIN)
async def admins_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admins command"""
    user = update.effective_user
    
    admins = db.get_all_admins()
    
    text = "👑 *MANAJEMEN ADMIN*\n\n"
    text += f"Total Admin: {len(admins)}\n\n"
    
    for admin in admins:
        role_emoji = "⭐" if admin.get('role') == 'super_admin' else "👑"
        name = admin.get('first_name') or f"User {admin['user_id']}"
        username = f"@{admin['username']}" if admin.get('username') else ""
        
        text += f"{role_emoji} `{admin['user_id']}` - {name} {username}\n"
        text += f"   📅 Added: {admin['added_date'][:10]}\n"
        
        if admin.get('role') != 'super_admin':
            perms = []
            if admin.get('can_manage_users'): perms.append("👥")
            if admin.get('can_manage_posts'): perms.append("📅")
            if admin.get('can_broadcast'): perms.append("📢")
            if admin.get('can_view_stats'): perms.append("📊")
            text += f"   🔑 Permissions: {' '.join(perms)}\n"
        text += "\n"
    
    keyboard = [
        [InlineKeyboardButton("➕ TAMBAH ADMIN", callback_data='admins_add')],
        [InlineKeyboardButton("✏️ EDIT PERMISSIONS", callback_data='admins_edit')],
        [InlineKeyboardButton("➖ HAPUS ADMIN", callback_data='admins_remove')],
        [InlineKeyboardButton("🔙 KEMBALI", callback_data='admin_dashboard')]
    ]
    
    await update.message.reply_text(
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    db.log_interaction(user.id, '/admins')

@role_required(UserRole.SUPER_ADMIN)
async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /settings command"""
    user = update.effective_user
    
    settings = db.get_all_settings()
    
    text = "⚙️ *PENGATURAN BOT*\n\n"
    
    categories = {
        'general': [],
        'features': [],
        'broadcast': [],
        'limits': [],
        'messages': []
    }
    
    for setting in settings:
        key = setting['key']
        value = setting['value']
        desc = setting.get('description', key)
        
        if key.startswith('welcome') or key.startswith('auto') or key.startswith('broadcast_enabled'):
            categories['features'].append((key, value, desc))
        elif key.startswith('broadcast_'):
            categories['broadcast'].append((key, value, desc))
        elif key.startswith('max_') or key.endswith('_per_page'):
            categories['limits'].append((key, value, desc))
        elif key.startswith('message_'):
            categories['messages'].append((key, value, desc))
        else:
            categories['general'].append((key, value, desc))
    
    for category, items in categories.items():
        if items:
            text += f"*{category.upper()}*\n"
            for key, value, desc in items:
                text += f"• {desc}: `{value}`\n"
            text += "\n"
    
    text += "Gunakan /set [key] [value] untuk mengubah\n"
    text += "Contoh: /set bot_name 'Nama Baru'"
    
    keyboard = [[InlineKeyboardButton("🔙 KEMBALI", callback_data='admin_dashboard')]]
    
    await update.message.reply_text(
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    db.log_interaction(user.id, '/settings')

@role_required(UserRole.SUPER_ADMIN)
async def set_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /set command"""
    if len(context.args) < 2:
        await update.message.reply_text("❌ Gunakan: /set [key] [value]\nContoh: /set bot_name 'Nama Bot'")
        return
    
    key = context.args[0]
    value = ' '.join(context.args[1:]).strip("'\"")
    
    # Determine type
    if value.lower() in ['true', 'false']:
        value_type = 'boolean'
    elif value.isdigit():
        value_type = 'integer'
    else:
        try:
            float(value)
            value_type = 'float'
        except:
            value_type = 'string'
    
    if db.update_setting(key, value, update.effective_user.id, value_type):
        await update.message.reply_text(
            f"✅ Setting `{key}` diubah menjadi `{value}` (type: {value_type})",
            parse_mode=ParseMode.MARKDOWN
        )
        logger.info(f"⚙️ Setting {key} changed to {value} by {update.effective_user.id}")
    else:
        await update.message.reply_text(f"❌ Gagal mengubah setting `{key}`", parse_mode=ParseMode.MARKDOWN)

@role_required(UserRole.SUPER_ADMIN)
async def backup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /backup command"""
    user = update.effective_user
    
    msg = await update.message.reply_text("💾 Membuat backup database...")
    
    backup_file = db.backup_database()
    
    if backup_file:
        # Get file size
        size = os.path.getsize(backup_file)
        size_str = f"{size / 1024:.2f} KB" if size < 1024*1024 else f"{size / (1024*1024):.2f} MB"
        
        await msg.edit_text(
            f"✅ *Backup Berhasil*\n\n"
            f"📁 File: `{backup_file}`\n"
            f"📦 Size: {size_str}\n"
            f"🕐 Waktu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Send file
        await context.bot.send_document(
            chat_id=user.id,
            document=open(backup_file, 'rb'),
            filename=os.path.basename(backup_file),
            caption="💾 Backup Database"
        )
    else:
        await msg.edit_text("❌ Gagal membuat backup.")
    
    db.log_interaction(user.id, '/backup')

# ==================== BROADCAST COMMANDS ====================

@role_required(UserRole.ADMIN)
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /broadcast command"""
    user = update.effective_user
    perms = db.get_admin_permissions(user.id) if db.get_user_role(user.id) == UserRole.ADMIN else {'can_broadcast': True}
    
    if not perms.get('can_broadcast') and db.get_user_role(user.id) != UserRole.SUPER_ADMIN:
        await update.message.reply_text("❌ Anda tidak memiliki izin untuk broadcast.")
        return
    
    # Check daily limit
    if db.get_user_role(user.id) != UserRole.SUPER_ADMIN:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM broadcast_messages 
                WHERE created_by = ? AND date(created_at) = date("now")
            ''', (user.id,))
            today_count = cursor.fetchone()[0]
            
            max_per_day = db.get_setting_with_type('max_broadcast_per_day', 5)
            
            if today_count >= max_per_day:
                await update.message.reply_text(
                    f"❌ Anda telah mencapai batas broadcast hari ini ({max_per_day}).\n"
                    f"Coba lagi besok atau hubungi super admin."
                )
                return
    
    text = (
        "📢 *SISTEM BROADCAST*\n\n"
        "Pilih jenis broadcast:\n\n"
        "1️⃣ *Broadcast Teks* - Kirim pesan teks ke semua user\n"
        "2️⃣ *Broadcast dengan Gambar* - Kirim pesan + gambar\n"
        "3️⃣ *Broadcast Terjadwal* - Jadwalkan untuk nanti\n"
        "4️⃣ *Broadcast Template* - Gunakan template yang ada\n"
        "5️⃣ *Lihat Riwayat* - Lihat broadcast sebelumnya\n\n"
        "Klik tombol di bawah untuk memulai:"
    )
    
    keyboard = [
        [InlineKeyboardButton("📝 BROADCAST TEKS", callback_data='broadcast_text')],
        [InlineKeyboardButton("🖼️ BROADCAST + GAMBAR", callback_data='broadcast_image')],
        [InlineKeyboardButton("⏰ BROADCAST TERJADWAL", callback_data='broadcast_schedule')],
        [InlineKeyboardButton("📋 PAKAI TEMPLATE", callback_data='broadcast_template')],
        [InlineKeyboardButton("📊 LIHAT RIWAYAT", callback_data='broadcast_history')],
        [InlineKeyboardButton("🔙 KEMBALI", callback_data='admin_dashboard')]
    ]
    
    await update.message.reply_text(
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    db.log_interaction(user.id, '/broadcast')

# ==================== AUTO POST COMMANDS ====================

@role_required(UserRole.ADMIN)
async def posts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /posts command"""
    user = update.effective_user
    perms = db.get_admin_permissions(user.id) if db.get_user_role(user.id) == UserRole.ADMIN else {'can_manage_posts': True}
    
    if not perms.get('can_manage_posts') and db.get_user_role(user.id) != UserRole.SUPER_ADMIN:
        await update.message.reply_text("❌ Anda tidak memiliki izin untuk mengelola auto post.")
        return
    
    posts = db.get_all_posts(include_inactive=True)
    
    text = "📅 *MANAJEMEN AUTO POST*\n\n"
    
    if posts:
        for post in posts:
            status = "✅ AKTIF" if post['is_active'] else "❌ NONAKTIF"
            text += f"🆔 *{post['post_id']}* | {post['time']} | {status}\n"
            preview = post['text'][:50] + ('...' if len(post['text']) > 50 else '')
            text += f"   `{preview}`\n"
            if post.get('image_url'):
                text += f"   📷 Ada Gambar\n"
            if post.get('category'):
                text += f"   📂 Kategori: {post['category']}\n"
            text += "\n"
    else:
        text += "Belum ada jadwal tersedia.\n\n"
    
    text += "Pilih menu di bawah:"
    
    keyboard = [
        [InlineKeyboardButton("➕ TAMBAH JADWAL", callback_data='posts_add')],
        [InlineKeyboardButton("✏️ EDIT JADWAL", callback_data='posts_edit')],
        [InlineKeyboardButton("❌ HAPUS JADWAL", callback_data='posts_delete')],
        [InlineKeyboardButton("✅ AKTIFKAN/NONAKTIFKAN", callback_data='posts_toggle')],
        [InlineKeyboardButton("📋 LIHAT SEMUA", callback_data='posts_list')],
        [InlineKeyboardButton("📂 BY CATEGORY", callback_data='posts_categories')],
        [InlineKeyboardButton("🔙 KEMBALI", callback_data='admin_dashboard')]
    ]
    
    await update.message.reply_text(
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    db.log_interaction(user.id, '/posts')

# ==================== STATISTICS COMMAND ====================

@role_required(UserRole.ADMIN)
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command"""
    user = update.effective_user
    perms = db.get_admin_permissions(user.id) if db.get_user_role(user.id) == UserRole.ADMIN else {'can_view_stats': True}
    
    if not perms.get('can_view_stats') and db.get_user_role(user.id) != UserRole.SUPER_ADMIN:
        await update.message.reply_text("❌ Anda tidak memiliki izin untuk melihat statistik.")
        return
    
    user_stats = db.get_user_stats()
    broadcast_stats = db.get_broadcast_stats()
    posts = db.get_all_posts()
    
    # Get today's interactions
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM user_interactions WHERE date(timestamp) = date("now")')
        interactions_today = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM user_interactions')
        total_interactions = cursor.fetchone()[0]
        
        # Top commands
        cursor.execute('''
            SELECT command, COUNT(*) as count 
            FROM user_interactions 
            GROUP BY command 
            ORDER BY count DESC 
            LIMIT 5
        ''')
        top_commands = [dict(row) for row in cursor.fetchall()]
    
    text = (
        "📊 *STATISTIK BOT LENGKAP*\n\n"
        "👥 *USER STATISTICS*\n"
        f"• Total User: {user_stats['total']}\n"
        f"• User Baru Hari Ini: {user_stats['today']}\n"
        f"• User Baru Minggu Ini: {user_stats['week']}\n"
        f"• User Baru Bulan Ini: {user_stats['month']}\n"
        f"• User Aktif (24h): {user_stats['active_24h']}\n"
        f"• User Aktif (7 hari): {user_stats['active_week']}\n"
        f"• User Diblokir: {user_stats['blocked']}\n"
        f"• User Dibanned: {user_stats['banned']}\n\n"
    )
    
    if user_stats['languages']:
        text += "🌍 *Top Languages*\n"
        for lang in user_stats['languages']:
            text += f"• {lang['language_code']}: {lang['count']} user\n"
        text += "\n"
    
    text += (
        "📅 *AUTO POST*\n"
        f"• Total Jadwal: {len(posts)}\n"
        f"• Jadwal Aktif: {sum(1 for p in posts if p['is_active'])}\n\n"
        "📢 *BROADCAST*\n"
        f"• Total Broadcast: {broadcast_stats['total']}\n"
        f"• Broadcast Terkirim: {broadcast_stats['sent']}\n"
        f"• Terjadwal: {broadcast_stats['scheduled']}\n"
        f"• Total Pesan Terkirim: {broadcast_stats['total_success']}\n"
        f"• Success Rate: {broadcast_stats['success_rate']:.1f}%\n\n"
        "📋 *INTERAKSI*\n"
        f"• Interaksi Hari Ini: {interactions_today}\n"
        f"• Total Interaksi: {total_interactions}\n"
    )
    
    if top_commands:
        text += "\n📌 *Top Commands*\n"
        for cmd in top_commands:
            text += f"• /{cmd['command']}: {cmd['count']}x\n"
    
    text += f"\n⚙️ *VERSI BOT*\n• Ultimate Pro v3.0"
    
    keyboard = [[InlineKeyboardButton("🔙 KEMBALI", callback_data='admin_dashboard')]]
    
    await update.message.reply_text(
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    db.log_interaction(user.id, '/stats')

# ==================== BUTTON CALLBACK HANDLER ====================

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all button callbacks"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    data = query.data
    
    logger.info(f"🔘 Button {data} clicked by {user.first_name} (ID: {user.id})")
    
    try:
        # ========== USER BUTTONS ==========
        if data == "login":
            text = "🔐 *Link Login*\n\nKlik tombol di bawah untuk login:"
            keyboard = [[InlineKeyboardButton("🔐 LOGIN SEKARANG", url=config.get('urls.login'))]]
            await query.message.reply_text(
                text=text, 
                parse_mode=ParseMode.MARKDOWN, 
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            await query.delete_message()
        
        elif data == "daftar":
            text = "📝 *Link Daftar*\n\nKlik tombol di bawah untuk mendaftar:"
            keyboard = [[InlineKeyboardButton("📝 DAFTAR SEKARANG", url=config.get('urls.daftar'))]]
            await query.message.reply_text(
                text=text, 
                parse_mode=ParseMode.MARKDOWN, 
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            await query.delete_message()
        
        elif data == "claim":
            text = "🎁 *Claim Event Parlay*\n\nKlik tombol di bawah untuk klaim bonus:"
            keyboard = [[InlineKeyboardButton("🎁 CLAIM BONUS", url=config.get('urls.claim'))]]
            await query.message.reply_text(
                text=text, 
                parse_mode=ParseMode.MARKDOWN, 
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            await query.delete_message()
        
        elif data == "promo":
            await send_promo(query.message, context)
            await query.delete_message()
        
        elif data == "back_to_menu":
            await start_command(update, context)
        
        # ========== ADMIN DASHBOARD ==========
        elif data == "admin_dashboard":
            if not db.is_admin(user.id):
                await query.message.reply_text("❌ Akses ditolak")
                return
            
            role = db.get_user_role(user.id)
            user_stats = db.get_user_stats()
            posts = db.get_all_posts()
            active_posts = sum(1 for p in posts if p['is_active'])
            
            text = (
                "⚙️ *DASHBOARD ADMIN*\n\n"
                f"👤 *Admin:* {user.first_name}\n"
                f"🆔 *ID:* `{user.id}`\n"
                f"👑 *Level:* {'⭐ SUPER ADMIN' if role == UserRole.SUPER_ADMIN else '👑 ADMIN'}\n\n"
                f"📊 *STATISTIK*\n"
                f"• Total User: {user_stats['total']}\n"
                f"• User Baru Hari Ini: {user_stats['today']}\n"
                f"• User Aktif 24h: {user_stats['active_24h']}\n"
                f"• Total Jadwal: {len(posts)}\n"
                f"• Jadwal Aktif: {active_posts}\n"
            )
            
            keyboard = []
            perms = db.get_admin_permissions(user.id) if role == UserRole.ADMIN else {}
            
            if role == UserRole.SUPER_ADMIN or perms.get('can_manage_users'):
                keyboard.append([InlineKeyboardButton("👥 MANAJEMEN USER", callback_data='admin_users')])
            if role == UserRole.SUPER_ADMIN or perms.get('can_broadcast'):
                keyboard.append([InlineKeyboardButton("📢 BROADCAST", callback_data='admin_broadcast')])
            if role == UserRole.SUPER_ADMIN or perms.get('can_manage_posts'):
                keyboard.append([InlineKeyboardButton("📅 AUTO POST", callback_data='admin_posts')])
            if role == UserRole.SUPER_ADMIN or perms.get('can_view_stats'):
                keyboard.append([InlineKeyboardButton("📊 STATISTIK", callback_data='admin_stats')])
                keyboard.append([InlineKeyboardButton("📋 LOG AKTIVITAS", callback_data='admin_logs')])
            
            if role == UserRole.SUPER_ADMIN:
                keyboard.extend([
                    [InlineKeyboardButton("👑 KELOLA ADMIN", callback_data='admin_manage_admins')],
                    [InlineKeyboardButton("⚙️ PENGATURAN", callback_data='admin_settings')],
                    [InlineKeyboardButton("💾 BACKUP & RESTORE", callback_data='admin_backup')],
                    [InlineKeyboardButton("📝 TEMPLATE", callback_data='admin_templates')],
                ])
            
            keyboard.append([InlineKeyboardButton("🔙 KEMBALI KE MENU", callback_data='back_to_menu')])
            
            await query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        elif data == "admin_users":
            if not db.is_admin(user.id):
                return
            
            users = db.get_all_users(limit=10)
            total = db.get_user_count()['total']
            
            text = f"👥 *MANAJEMEN USER*\n\nTotal User: {total}\n\n10 User Terbaru:\n\n"
            
            for u in users:
                status = "⛔" if u.get('is_blocked') else "✅"
                banned = "🚫" if u.get('is_banned') else ""
                role = "👑" if db.is_admin(u['user_id']) else "👤"
                text += f"{status}{banned}{role} `{u['user_id']}` - {u['first_name']}"
                if u.get('username'):
                    text += f" @{u['username']}"
                text += f"\n   📅 {u['joined_date'][:10]}\n"
            
            keyboard = [
                [InlineKeyboardButton("📋 LIHAT SEMUA", callback_data='users_page_1')],
                [InlineKeyboardButton("🔍 SEARCH USER", callback_data='user_search')],
                [InlineKeyboardButton("📊 STATISTIK USER", callback_data='user_stats')],
            ]
            
            if db.is_super_admin(user.id):
                keyboard.append([InlineKeyboardButton("⛔ BLOKIR USER", callback_data='user_block')])
                keyboard.append([InlineKeyboardButton("🚫 BAN USER", callback_data='user_ban')])
            
            keyboard.append([InlineKeyboardButton("🔙 KEMBALI", callback_data='admin_dashboard')])
            
            await query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        elif data == "admin_broadcast":
            if not db.is_admin(user.id):
                return
            
            # Check if admin can broadcast
            if db.get_user_role(user.id) == UserRole.ADMIN:
                perms = db.get_admin_permissions(user.id)
                if not perms.get('can_broadcast'):
                    await query.message.reply_text("❌ Anda tidak memiliki izin untuk broadcast.")
                    return
            
            stats = db.get_broadcast_stats()
            
            text = (
                "📢 *SISTEM BROADCAST*\n\n"
                f"📊 *STATISTIK*\n"
                f"• Total Broadcast: {stats['total']}\n"
                f"• Terkirim: {stats['sent']}\n"
                f"• Terjadwal: {stats['scheduled']}\n"
                f"• Success Rate: {stats['success_rate']:.1f}%\n\n"
                "Pilih jenis broadcast:"
            )
            
            keyboard = [
                [InlineKeyboardButton("📝 BROADCAST TEKS", callback_data='broadcast_text')],
                [InlineKeyboardButton("🖼️ BROADCAST + GAMBAR", callback_data='broadcast_image')],
                [InlineKeyboardButton("⏰ BROADCAST TERJADWAL", callback_data='broadcast_schedule')],
                [InlineKeyboardButton("📋 PAKAI TEMPLATE", callback_data='broadcast_template')],
                [InlineKeyboardButton("📊 LIHAT RIWAYAT", callback_data='broadcast_history')],
                [InlineKeyboardButton("🔙 KEMBALI", callback_data='admin_dashboard')]
            ]
            
            await query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        elif data == "admin_posts":
            if not db.is_admin(user.id):
                return
            
            # Check permissions
            if db.get_user_role(user.id) == UserRole.ADMIN:
                perms = db.get_admin_permissions(user.id)
                if not perms.get('can_manage_posts'):
                    await query.message.reply_text("❌ Anda tidak memiliki izin untuk mengelola auto post.")
                    return
            
            posts = db.get_all_posts(include_inactive=True)
            
            text = "📅 *MANAJEMEN AUTO POST*\n\n"
            
            if posts:
                categories = {}
                for post in posts:
                    cat = post.get('category', 'general')
                    if cat not in categories:
                        categories[cat] = []
                    categories[cat].append(post)
                
                for cat, cat_posts in categories.items():
                    text += f"📂 *{cat.upper()}* ({len(cat_posts)})\n"
                    for post in cat_posts[:3]:  # Show max 3 per category
                        status = "✅" if post['is_active'] else "❌"
                        text += f"  {status} ID {post['post_id']}: {post['time']}\n"
                    if len(cat_posts) > 3:
                        text += f"  ...dan {len(cat_posts)-3} lainnya\n"
                    text += "\n"
            else:
                text += "Belum ada jadwal.\n\n"
            
            keyboard = [
                [InlineKeyboardButton("➕ TAMBAH JADWAL", callback_data='posts_add')],
                [InlineKeyboardButton("✏️ EDIT JADWAL", callback_data='posts_edit')],
                [InlineKeyboardButton("❌ HAPUS JADWAL", callback_data='posts_delete')],
                [InlineKeyboardButton("🔄 AKTIF/NONAKTIF", callback_data='posts_toggle')],
                [InlineKeyboardButton("📋 LIHAT SEMUA", callback_data='posts_list')],
                [InlineKeyboardButton("🔙 KEMBALI", callback_data='admin_dashboard')]
            ]
            
            await query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        elif data == "admin_stats":
            if not db.is_admin(user.id):
                return
            
            # Check permissions
            if db.get_user_role(user.id) == UserRole.ADMIN:
                perms = db.get_admin_permissions(user.id)
                if not perms.get('can_view_stats'):
                    await query.message.reply_text("❌ Anda tidak memiliki izin untuk melihat statistik.")
                    return
            
            user_stats = db.get_user_stats()
            posts = db.get_all_posts()
            broadcast_stats = db.get_broadcast_stats()
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM user_interactions WHERE date(timestamp) = date("now")')
                interactions_today = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM admin_logs WHERE date(timestamp) = date("now")')
                logs_today = cursor.fetchone()[0]
            
            text = (
                "📊 *STATISTIK BOT*\n\n"
                "👥 *USER*\n"
                f"• Total: {user_stats['total']}\n"
                f"• Hari Ini: {user_stats['today']}\n"
                f"• Aktif 24h: {user_stats['active_24h']}\n"
                f"• Diblokir: {user_stats['blocked']}\n"
                f"• Dibanned: {user_stats['banned']}\n\n"
                "📅 *AUTO POST*\n"
                f"• Total Jadwal: {len(posts)}\n"
                f"• Aktif: {sum(1 for p in posts if p['is_active'])}\n\n"
                "📢 *BROADCAST*\n"
                f"• Total: {broadcast_stats['total']}\n"
                f"• Terkirim: {broadcast_stats['sent']}\n"
                f"• Success Rate: {broadcast_stats['success_rate']:.1f}%\n\n"
                "📋 *AKTIVITAS*\n"
                f"• Interaksi Hari Ini: {interactions_today}\n"
                f"• Log Admin Hari Ini: {logs_today}\n"
            )
            
            keyboard = [[InlineKeyboardButton("🔙 KEMBALI", callback_data='admin_dashboard')]]
            
            await query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        elif data == "admin_logs":
            if not db.is_admin(user.id):
                return
            
            logs = db.get_admin_logs(20)
            
            text = "📋 *LOG AKTIVITAS ADMIN (20 Terakhir)*\n\n"
            
            if logs:
                for log in logs:
                    admin = log.get('username') or log.get('first_name') or f"User {log['admin_id']}"
                    text += f"🕐 {log['timestamp'][:16]} - {admin}\n"
                    text += f"   ⚡ {log['action']} - {log.get('target_type', 'system')}\n"
                    if log.get('details'):
                        text += f"   📝 {log['details'][:50]}\n"
                    text += "\n"
            else:
                text += "Belum ada log.\n"
            
            keyboard = [[InlineKeyboardButton("🔙 KEMBALI", callback_data='admin_dashboard')]]
            
            await query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        elif data == "admin_manage_admins":
            if not db.is_super_admin(user.id):
                await query.message.reply_text("❌ Hanya super admin!")
                return
            
            admins = db.get_all_admins()
            
            text = "👑 *MANAJEMEN ADMIN*\n\n"
            text += f"Total Admin: {len(admins)}\n\n"
            
            for admin in admins[:5]:
                role_emoji = "⭐" if admin.get('role') == 'super_admin' else "👑"
                name = admin.get('first_name') or f"User {admin['user_id']}"
                text += f"{role_emoji} `{admin['user_id']}` - {name}\n"
            
            if len(admins) > 5:
                text += f"\n...dan {len(admins)-5} lainnya\n"
            
            keyboard = [
                [InlineKeyboardButton("📋 LIHAT SEMUA", callback_data='admins_list')],
                [InlineKeyboardButton("➕ TAMBAH ADMIN", callback_data='admins_add')],
                [InlineKeyboardButton("✏️ EDIT PERMISSIONS", callback_data='admins_edit')],
                [InlineKeyboardButton("➖ HAPUS ADMIN", callback_data='admins_remove')],
                [InlineKeyboardButton("🔙 KEMBALI", callback_data='admin_dashboard')]
            ]
            
            await query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        elif data == "admin_settings":
            if not db.is_super_admin(user.id):
                return
            
            settings = db.get_all_settings()[:10]
            
            text = "⚙️ *PENGATURAN (10 Pertama)*\n\n"
            
            for setting in settings:
                key = setting['key']
                value = setting['value']
                typ = setting.get('type', 'string')
                text += f"• `{key}`: `{value}` ({typ})\n"
            
            text += "\nGunakan /set [key] [value] untuk mengubah"
            
            keyboard = [[InlineKeyboardButton("🔙 KEMBALI", callback_data='admin_dashboard')]]
            
            await query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        elif data == "admin_backup":
            if not db.is_super_admin(user.id):
                return
            
            text = (
                "💾 *BACKUP & RESTORE*\n\n"
                "Pilih opsi:"
            )
            
            keyboard = [
                [InlineKeyboardButton("📤 BUAT BACKUP", callback_data='backup_create')],
                [InlineKeyboardButton("📥 LIHAT BACKUP", callback_data='backup_list')],
                [InlineKeyboardButton("🔄 RESTORE", callback_data='backup_restore')],
                [InlineKeyboardButton("🔙 KEMBALI", callback_data='admin_dashboard')]
            ]
            
            await query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        elif data == "admin_templates":
            if not db.is_super_admin(user.id):
                return
            
            templates = db.get_templates()
            
            text = "📝 *TEMPLATE PESAN*\n\n"
            
            if templates:
                for t in templates[:5]:
                    text += f"• *{t['name']}* ({t['type']})\n"
                    text += f"  📊 Used: {t['use_count']}x\n"
                if len(templates) > 5:
                    text += f"\n...dan {len(templates)-5} lainnya\n"
            else:
                text += "Belum ada template.\n"
            
            keyboard = [
                [InlineKeyboardButton("➕ BUAT TEMPLATE", callback_data='template_add')],
                [InlineKeyboardButton("📋 LIHAT SEMUA", callback_data='template_list')],
                [InlineKeyboardButton("🔙 KEMBALI", callback_data='admin_dashboard')]
            ]
            
            await query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        # ========== PAGINATION ==========
        elif data.startswith('users_page_'):
            if not db.is_admin(user.id):
                return
            
            page = int(data.split('_')[2])
            per_page = db.get_setting_with_type('users_per_page', 10)
            offset = (page - 1) * per_page
            
            users = db.get_all_users(limit=per_page, offset=offset)
            total = db.get_user_count()['total']
            total_pages = (total + per_page - 1) // per_page
            
            text = f"📋 *DAFTAR USER (Halaman {page}/{total_pages})*\n\n"
            
            for u in users:
                status = "⛔" if u.get('is_blocked') else "✅"
                banned = "🚫" if u.get('is_banned') else ""
                role = "👑" if db.is_admin(u['user_id']) else "👤"
                text += f"{status}{banned}{role} `{u['user_id']}` - {u['first_name']}"
                if u.get('username'):
                    text += f" @{u['username']}"
                text += f"\n   📅 {u['joined_date'][:10]}\n"
            
            keyboard = []
            nav_row = []
            if page > 1:
                nav_row.append(InlineKeyboardButton("◀️", callback_data=f'users_page_{page-1}'))
            nav_row.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data='noop'))
            if page < total_pages:
                nav_row.append(InlineKeyboardButton("▶️", callback_data=f'users_page_{page+1}'))
            if nav_row:
                keyboard.append(nav_row)
            
            keyboard.append([InlineKeyboardButton("🔙 KEMBALI", callback_data='admin_users')])
            
            await query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        # ========== BROADCAST FLOW ==========
        elif data == "broadcast_text":
            if not db.is_admin(user.id):
                return
            
            context.user_data['broadcast_step'] = 'text'
            await query.message.edit_text(
                "📝 *BROADCAST TEKS*\n\n"
                "Silakan kirim pesan teks yang ingin di-broadcast.\n\n"
                "Format *Markdown* didukung.\n"
                f"Maksimal {db.get_setting('max_broadcast_length', 4096)} karakter.\n\n"
                "Ketik *batal* untuk membatalkan.",
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif data == "broadcast_image":
            if not db.is_admin(user.id):
                return
            
            context.user_data['broadcast_step'] = 'waiting_image'
            await query.message.edit_text(
                "🖼️ *BROADCAST DENGAN GAMBAR*\n\n"
                "Kirim gambar yang ingin di-broadcast.\n\n"
                "Ketik *batal* untuk membatalkan.",
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif data == "broadcast_schedule":
            if not db.is_admin(user.id):
                return
            
            context.user_data['broadcast_step'] = 'schedule_time'
            await query.message.edit_text(
                "⏰ *BROADCAST TERJADWAL*\n\n"
                "Masukkan waktu jadwal (format: YYYY-MM-DD HH:MM)\n"
                "Contoh: 2024-12-31 20:00\n\n"
                "Ketik *batal* untuk membatalkan.",
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif data == "broadcast_template":
            if not db.is_admin(user.id):
                return
            
            templates = db.get_templates('text')
            
            if not templates:
                await query.message.edit_text(
                    "❌ Belum ada template tersedia.\n\n"
                    "Hubungi super admin untuk membuat template.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 KEMBALI", callback_data='admin_broadcast')
                    ]])
                )
                return
            
            text = "📋 *PILIH TEMPLATE*\n\n"
            
            keyboard = []
            for t in templates[:8]:
                keyboard.append([InlineKeyboardButton(
                    f"{t['name']} (used: {t['use_count']}x)", 
                    callback_data=f'template_use_{t["template_id"]}'
                )])
            
            keyboard.append([InlineKeyboardButton("🔙 KEMBALI", callback_data='admin_broadcast')])
            
            await query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        elif data == "broadcast_history":
            if not db.is_admin(user.id):
                return
            
            broadcasts = db.get_all_broadcasts(10)
            
            if not broadcasts:
                text = "📋 *RIWAYAT BROADCAST*\n\nBelum ada broadcast."
            else:
                text = "📋 *RIWAYAT BROADCAST (10 Terakhir)*\n\n"
                for b in broadcasts:
                    status_emoji = {
                        'draft': '📝', 'scheduled': '⏰', 
                        'sending': '📤', 'sent': '✅', 'cancelled': '❌',
                        'failed': '❌'
                    }.get(b['status'], '📋')
                    
                    creator = b.get('creator_name') or f"User {b['created_by']}"
                    date = b['created_at'][:16]
                    
                    text += f"{status_emoji} {date} - {creator}\n"
                    text += f"   📊 {b['success_count']}/{b['total_recipients'] or 0} sukses\n"
                    
                    if b.get('scheduled_time'):
                        text += f"   ⏰ Jadwal: {b['scheduled_time'][:16]}\n"
                    
                    if b['message_text']:
                        preview = b['message_text'][:50].replace('\n', ' ')
                        text += f"   `{preview}...`\n"
                    text += "\n"
            
            keyboard = [[InlineKeyboardButton("🔙 KEMBALI", callback_data='admin_broadcast')]]
            
            await query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        # ========== POSTS BUTTONS ==========
        elif data == "posts_add":
            if not db.is_admin(user.id):
                return
            
            context.user_data['post_step'] = 'time'
            await query.message.edit_text(
                "➕ *TAMBAH JADWAL AUTO POST*\n\n"
                "Langkah 1/5: Masukkan waktu (HH:MM)\n"
                "Contoh: `14:30`\n\n"
                "Ketik *batal* untuk membatalkan.",
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif data == "posts_list":
            if not db.is_admin(user.id):
                return
            
            posts = db.get_all_posts(include_inactive=True)
            
            if not posts:
                text = "📋 *SEMUA JADWAL*\n\nBelum ada jadwal."
            else:
                text = "📋 *SEMUA JADWAL AUTO POST*\n\n"
                for post in posts:
                    status = "✅" if post['is_active'] else "❌"
                    text += f"{status} *ID {post['post_id']}* | {post['time']}\n"
                    text += f"   `{post['text'][:100]}`\n"
                    if post.get('image_url'):
                        text += f"   📷 Gambar: {post['image_url'][:50]}...\n"
                    if post.get('category'):
                        text += f"   📂 Kategori: {post['category']}\n"
                    text += "\n"
            
            keyboard = [[InlineKeyboardButton("🔙 KEMBALI", callback_data='admin_posts')]]
            
            await query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        elif data == "posts_edit":
            if not db.is_admin(user.id):
                return
            
            context.user_data['post_action'] = 'edit'
            await query.message.edit_text(
                "✏️ *EDIT JADWAL*\n\n"
                "Masukkan ID jadwal yang ingin diedit:\n\n"
                "Ketik *batal* untuk membatalkan.",
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif data == "posts_delete":
            if not db.is_admin(user.id):
                return
            
            context.user_data['post_action'] = 'delete'
            await query.message.edit_text(
                "❌ *HAPUS JADWAL*\n\n"
                "Masukkan ID jadwal yang ingin dihapus:\n\n"
                "Ketik *batal* untuk membatalkan.",
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif data == "posts_toggle":
            if not db.is_admin(user.id):
                return
            
            context.user_data['post_action'] = 'toggle'
            await query.message.edit_text(
                "🔄 *AKTIFKAN/NONAKTIFKAN JADWAL*\n\n"
                "Masukkan ID jadwal:\n\n"
                "Ketik *batal* untuk membatalkan.",
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif data == "posts_categories":
            if not db.is_admin(user.id):
                return
            
            posts = db.get_all_posts(include_inactive=True)
            categories = {}
            
            for post in posts:
                cat = post.get('category', 'general')
                if cat not in categories:
                    categories[cat] = 0
                categories[cat] += 1
            
            text = "📂 *KATEGORI AUTO POST*\n\n"
            
            for cat, count in categories.items():
                text += f"• {cat}: {count} jadwal\n"
            
            keyboard = [[InlineKeyboardButton("🔙 KEMBALI", callback_data='admin_posts')]]
            
            await query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        # ========== ADMINS BUTTONS ==========
        elif data == "admins_list":
            if not db.is_super_admin(user.id):
                return
            
            admins = db.get_all_admins()
            
            text = "👑 *DAFTAR ADMIN*\n\n"
            
            if not admins:
                text += "Belum ada admin selain super admin."
            else:
                for admin in admins:
                    role_emoji = "⭐" if admin.get('role') == 'super_admin' else "👑"
                    name = admin.get('first_name') or f"User {admin['user_id']}"
                    username = f"@{admin['username']}" if admin.get('username') else ""
                    
                    text += f"{role_emoji} `{admin['user_id']}` - {name} {username}\n"
                    text += f"   📅 Added: {admin['added_date'][:10]}\n"
                    
                    if admin.get('role') != 'super_admin':
                        perms = []
                        if admin.get('can_manage_users'): perms.append("👥")
                        if admin.get('can_manage_posts'): perms.append("📅")
                        if admin.get('can_broadcast'): perms.append("📢")
                        if admin.get('can_view_stats'): perms.append("📊")
                        text += f"   🔑 {', '.join(perms)}\n"
                    text += "\n"
            
            keyboard = [[InlineKeyboardButton("🔙 KEMBALI", callback_data='admin_manage_admins')]]
            
            await query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        elif data == "admins_add":
            if not db.is_super_admin(user.id):
                return
            
            context.user_data['admin_step'] = 'waiting_id'
            await query.message.edit_text(
                "➕ *TAMBAH ADMIN*\n\n"
                "Masukkan User ID yang ingin dijadikan admin:\n\n"
                "Ketik *batal* untuk membatalkan.",
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif data == "admins_edit":
            if not db.is_super_admin(user.id):
                return
            
            context.user_data['admin_step'] = 'edit_id'
            await query.message.edit_text(
                "✏️ *EDIT PERMISSIONS ADMIN*\n\n"
                "Masukkan User ID admin yang ingin diedit:\n\n"
                "Ketik *batal* untuk membatalkan.",
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif data == "admins_remove":
            if not db.is_super_admin(user.id):
                return
            
            context.user_data['admin_step'] = 'remove_id'
            await query.message.edit_text(
                "➖ *HAPUS ADMIN*\n\n"
                "Masukkan User ID admin yang ingin dihapus:\n\n"
                "Ketik *batal* untuk membatalkan.",
                parse_mode=ParseMode.MARKDOWN
            )
        
        # ========== BACKUP BUTTONS ==========
        elif data == "backup_create":
            if not db.is_super_admin(user.id):
                return
            
            await query.message.edit_text("💾 Membuat backup...")
            
            backup_file = db.backup_database()
            
            if backup_file:
                size = os.path.getsize(backup_file)
                size_str = f"{size / 1024:.2f} KB"
                
                await query.message.edit_text(
                    f"✅ *Backup Berhasil*\n\n"
                    f"File: `{backup_file}`\n"
                    f"Size: {size_str}",
                    parse_mode=ParseMode.MARKDOWN
                )
                
                await context.bot.send_document(
                    chat_id=user.id,
                    document=open(backup_file, 'rb'),
                    filename=os.path.basename(backup_file),
                    caption="💾 Database Backup"
                )
            else:
                await query.message.edit_text("❌ Gagal membuat backup.")
        
        # ========== USER ACTIONS ==========
        elif data == "user_stats":
            if not db.is_admin(user.id):
                return
            
            stats = db.get_user_stats()
            
            text = (
                "📊 *STATISTIK USER*\n\n"
                f"• Total User: {stats['total']}\n"
                f"• Hari Ini: {stats['today']}\n"
                f"• Minggu Ini: {stats['week']}\n"
                f"• Bulan Ini: {stats['month']}\n"
                f"• Aktif 24 Jam: {stats['active_24h']}\n"
                f"• Aktif 7 Hari: {stats['active_week']}\n"
                f"• Diblokir: {stats['blocked']}\n"
                f"• Dibanned: {stats['banned']}\n\n"
                "🌍 *Top Languages*\n"
            )
            
            for lang in stats['languages']:
                text += f"• {lang['language_code']}: {lang['count']} user\n"
            
            keyboard = [[InlineKeyboardButton("🔙 KEMBALI", callback_data='admin_users')]]
            
            await query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        elif data == "user_search":
            if not db.is_super_admin(user.id):
                return
            
            context.user_data['admin_action'] = 'search'
            await query.message.edit_text(
                "🔍 *SEARCH USER*\n\n"
                "Masukkan username atau nama yang ingin dicari:\n\n"
                "Ketik *batal* untuk membatalkan.",
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif data == "user_block":
            if not db.is_super_admin(user.id):
                return
            
            context.user_data['admin_action'] = 'block'
            await query.message.edit_text(
                "⛔ *BLOKIR USER*\n\n"
                "Masukkan User ID yang ingin diblokir:\n\n"
                "Ketik *batal* untuk membatalkan.",
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif data == "user_ban":
            if not db.is_super_admin(user.id):
                return
            
            context.user_data['admin_action'] = 'ban'
            await query.message.edit_text(
                "🚫 *BAN USER*\n\n"
                "Masukkan User ID yang ingin di-ban:\n\n"
                "Ketik *batal* untuk membatalkan.",
                parse_mode=ParseMode.MARKDOWN
            )
        
        # ========== CONFIRM BROADCAST ==========
        elif data.startswith('confirm_broadcast_'):
            if not db.is_admin(user.id):
                return
            
            broadcast_id = int(data.split('_')[2])
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM broadcast_messages WHERE broadcast_id = ?', (broadcast_id,))
                broadcast = dict(cursor.fetchone())
            
            await query.message.edit_text(
                "📢 *MENGIRIM BROADCAST...*\n\n"
                "Proses pengiriman sedang berlangsung. Ini akan memakan waktu beberapa saat.\n"
                "Anda akan mendapat notifikasi setelah selesai.",
                parse_mode=ParseMode.MARKDOWN
            )
            
            asyncio.create_task(
                broadcast_manager.send_broadcast(
                    context,
                    broadcast_id=broadcast_id,
                    message_text=broadcast['message_text'],
                    message_type=broadcast['message_type'],
                    file_id=broadcast['file_id'],
                    caption=broadcast['caption'],
                    buttons=json.loads(broadcast['buttons']) if broadcast['buttons'] else None
                )
            )
        
        # No operation button
        elif data == "noop":
            pass
        
    except Exception as e:
        logger.error(f"❌ Error in button_callback: {e}")
        await query.message.reply_text(
            "❌ Terjadi kesalahan. Silakan coba lagi nanti."
        )

# ==================== SEND PROMO FUNCTION ====================

async def send_promo(message, context):
    """Send promo message"""
    try:
        keyboard = [
            [InlineKeyboardButton("🤖 BOT OFFICIAL", url=config.get('urls.bot_official'))],
            [InlineKeyboardButton("📈 PREDIKSI JITU", url=config.get('urls.prediksi'))],
            [InlineKeyboardButton("📢 CHANNEL WA", url=config.get('urls.channel_wa'))],
            [InlineKeyboardButton("📢 CHANNEL TG", url=config.get('urls.channel_tg'))],
            [InlineKeyboardButton("🟢 KLAIM BONUS", url=config.get('urls.claim'))],
            [InlineKeyboardButton("🔙 KEMBALI KE MENU", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        image_url = config.get('images.default_promo')
        
        try:
            await message.reply_photo(
                photo=image_url,
                caption=PROMO_TEXT,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        except:
            await message.reply_text(
                text=PROMO_TEXT,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
                reply_markup=reply_markup
            )
    except Exception as e:
        logger.error(f"❌ Error sending promo: {e}")

# ==================== MESSAGE HANDLER ====================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all text messages"""
    user = update.effective_user
    text = update.message.text
    
    # Save user
    db.add_or_update_user(user)
    
    # Check if blocked/banned
    user_data = db.get_user(user.id)
    if user_data and (user_data.get('is_banned') or user_data.get('is_blocked')):
        return
    
    # ===== BROADCAST FLOW =====
    if 'broadcast_step' in context.user_data:
        step = context.user_data['broadcast_step']
        
        if text.lower() == 'batal':
            del context.user_data['broadcast_step']
            await update.message.reply_text("✅ Broadcast dibatalkan.")
            return
        
        if step == 'text':
            # Validate length
            max_length = db.get_setting_with_type('max_broadcast_length', 4096)
            if len(text) > max_length:
                await update.message.reply_text(
                    f"❌ Pesan terlalu panjang! Maksimal {max_length} karakter.\n"
                    f"Pesan Anda: {len(text)} karakter."
                )
                return
            
            broadcast_id = db.create_broadcast(
                created_by=user.id,
                message_text=text,
                message_type='text'
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("✅ KIRIM SEKARANG", callback_data=f'confirm_broadcast_{broadcast_id}'),
                    InlineKeyboardButton("❌ BATAL", callback_data='admin_broadcast')
                ]
            ]
            
            await update.message.reply_text(
                "📢 *KONFIRMASI BROADCAST*\n\n"
                f"Teks:\n{text}\n\n"
                f"Kirim sekarang?",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
            del context.user_data['broadcast_step']
        
        elif step == 'waiting_image':
            context.user_data['broadcast_step'] = 'waiting_caption'
            context.user_data['broadcast_image'] = text
            await update.message.reply_text(
                "📝 Kirim caption untuk gambar (atau ketik - untuk tanpa caption):"
            )
        
        elif step == 'waiting_caption':
            caption = text if text != '-' else None
            broadcast_id = db.create_broadcast(
                created_by=user.id,
                message_text=caption or "Promo Terbaru",
                message_type='photo',
                file_id=context.user_data.get('broadcast_image'),
                caption=caption
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("✅ KIRIM SEKARANG", callback_data=f'confirm_broadcast_{broadcast_id}'),
                    InlineKeyboardButton("❌ BATAL", callback_data='admin_broadcast')
                ]
            ]
            
            await update.message.reply_text(
                "📢 *KONFIRMASI BROADCAST*\n\n"
                "Broadcast dengan gambar siap dikirim.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
            del context.user_data['broadcast_step']
        
        elif step == 'schedule_time':
            try:
                schedule_time = datetime.strptime(text, '%Y-%m-%d %H:%M')
                if schedule_time < datetime.now():
                    await update.message.reply_text("❌ Waktu jadwal harus di masa depan!")
                    return
                
                context.user_data['broadcast_schedule'] = schedule_time
                context.user_data['broadcast_step'] = 'schedule_text'
                
                await update.message.reply_text(
                    "📝 Sekarang masukkan teks broadcast:"
                )
            except:
                await update.message.reply_text(
                    "❌ Format waktu salah! Gunakan YYYY-MM-DD HH:MM\n"
                    "Contoh: 2024-12-31 20:00"
                )
        
        elif step == 'schedule_text':
            schedule_time = context.user_data['broadcast_schedule']
            
            broadcast_id = db.create_broadcast(
                created_by=user.id,
                message_text=text,
                message_type='text'
            )
            
            db.schedule_broadcast(broadcast_id, schedule_time)
            
            await update.message.reply_text(
                f"✅ Broadcast dijadwalkan pada {schedule_time.strftime('%Y-%m-%d %H:%M')}."
            )
            
            del context.user_data['broadcast_step']
            del context.user_data['broadcast_schedule']
        
        return
    
    # ===== POST ADD FLOW =====
    if 'post_step' in context.user_data:
        step = context.user_data['post_step']
        
        if text.lower() == 'batal':
            del context.user_data['post_step']
            await update.message.reply_text("✅ Penambahan jadwal dibatalkan.")
            return
        
        if step == 'time':
            try:
                hour, minute = map(int, text.split(':'))
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    context.user_data['post_time'] = text
                    context.user_data['post_step'] = 'text'
                    await update.message.reply_text(
                        "Langkah 2/5: Masukkan teks yang ingin dikirim:"
                    )
                else:
                    await update.message.reply_text("❌ Format waktu salah! Gunakan HH:MM (00-23:00-59)")
            except:
                await update.message.reply_text("❌ Format waktu salah! Gunakan HH:MM")
        
        elif step == 'text':
            context.user_data['post_text'] = text
            context.user_data['post_step'] = 'image'
            await update.message.reply_text(
                "Langkah 3/5: Masukkan URL gambar (atau ketik - untuk tanpa gambar):"
            )
        
        elif step == 'image':
            image_url = None if text == '-' else text
            context.user_data['post_image'] = image_url
            context.user_data['post_step'] = 'button'
            await update.message.reply_text(
                "Langkah 4/5: Masukkan teks tombol (atau ketik - untuk tanpa tombol):"
            )
        
        elif step == 'button':
            if text != '-':
                context.user_data['post_button_text'] = text
                context.user_data['post_step'] = 'button_url'
                await update.message.reply_text(
                    "Masukkan URL untuk tombol tersebut:"
                )
            else:
                context.user_data['post_step'] = 'category'
                await update.message.reply_text(
                    "Langkah 5/5: Masukkan kategori (atau ketik - untuk default 'general'):"
                )
        
        elif step == 'button_url':
            context.user_data['post_button_url'] = text
            context.user_data['post_step'] = 'category'
            await update.message.reply_text(
                "Langkah 5/5: Masukkan kategori (atau ketik - untuk default 'general'):"
            )
        
        elif step == 'category':
            category = text if text != '-' else 'general'
            
            post_id = db.add_post(
                time_str=context.user_data['post_time'],
                text=context.user_data['post_text'],
                image_url=context.user_data.get('post_image'),
                button_text=context.user_data.get('post_button_text'),
                button_url=context.user_data.get('post_button_url'),
                created_by=user.id,
                category=category
            )
            
            await update.message.reply_text(
                f"✅ Jadwal ID {post_id} berhasil ditambahkan dalam kategori '{category}'!"
            )
            
            db.log_admin_action(user.id, 'add_post', 'auto_post', str(post_id), f"Added post at {context.user_data['post_time']}")
            del context.user_data['post_step']
        
        return
    
    # ===== POST ACTION FLOW =====
    if 'post_action' in context.user_data:
        action = context.user_data['post_action']
        
        if text.lower() == 'batal':
            del context.user_data['post_action']
            await update.message.reply_text("✅ Operasi dibatalkan.")
            return
        
        try:
            post_id = int(text)
            post = db.get_post(post_id)
            
            if not post:
                await update.message.reply_text(f"❌ Jadwal ID {post_id} tidak ditemukan.")
                del context.user_data['post_action']
                return
            
            if action == 'edit':
                context.user_data['edit_post_id'] = post_id
                context.user_data['post_step'] = 'time'
                await update.message.reply_text(
                    f"✏️ *EDIT JADWAL ID {post_id}*\n\n"
                    f"Data saat ini:\n"
                    f"Waktu: {post['time']}\n"
                    f"Kategori: {post.get('category', 'general')}\n"
                    f"Teks: {post['text'][:100]}...\n\n"
                    f"Masukkan waktu baru (HH:MM):",
                    parse_mode=ParseMode.MARKDOWN
                )
                del context.user_data['post_action']
            
            elif action == 'delete':
                if db.delete_post(post_id):
                    await update.message.reply_text(f"✅ Jadwal ID {post_id} telah dihapus.")
                    db.log_admin_action(user.id, 'delete_post', 'auto_post', str(post_id), "Deleted post")
                else:
                    await update.message.reply_text(f"❌ Gagal menghapus jadwal ID {post_id}.")
                del context.user_data['post_action']
            
            elif action == 'toggle':
                if db.toggle_post(post_id):
                    post = db.get_post(post_id)
                    status = "diaktifkan" if post['is_active'] else "dinonaktifkan"
                    await update.message.reply_text(f"✅ Jadwal ID {post_id} telah {status}.")
                    db.log_admin_action(user.id, 'toggle_post', 'auto_post', str(post_id), f"Post {status}")
                else:
                    await update.message.reply_text(f"❌ Gagal mengubah status jadwal ID {post_id}.")
                del context.user_data['post_action']
        
        except ValueError:
            await update.message.reply_text("❌ ID harus berupa angka!")
        
        return
    
    # ===== ADMIN ACTION FLOW =====
    if 'admin_action' in context.user_data:
        action = context.user_data['admin_action']
        
        if text.lower() == 'batal':
            del context.user_data['admin_action']
            await update.message.reply_text("✅ Operasi dibatalkan.")
            return
        
        if action == 'search':
            users = db.search_users(text)
            
            if not users:
                await update.message.reply_text(f"❌ Tidak ada user ditemukan untuk '{text}'.")
            else:
                result = f"🔍 *Hasil Pencarian: '{text}'*\n\n"
                for u in users[:10]:
                    status = "⛔" if u.get('is_blocked') else "✅"
                    banned = "🚫" if u.get('is_banned') else ""
                    result += f"{status}{banned} `{u['user_id']}` - {u['first_name']}"
                    if u.get('username'):
                        result += f" @{u['username']}"
                    result += f"\n"
                
                if len(users) > 10:
                    result += f"\n...dan {len(users)-10} lainnya"
                
                await update.message.reply_text(result, parse_mode=ParseMode.MARKDOWN)
            
            del context.user_data['admin_action']
            return
        
        try:
            target_id = int(text)
            
            if action == 'block':
                if target_id in SUPER_ADMINS:
                    await update.message.reply_text("❌ Tidak bisa memblokir super admin!")
                else:
                    if db.block_user(target_id, "Blocked by admin"):
                        await update.message.reply_text(f"✅ User `{target_id}` telah diblokir.", parse_mode=ParseMode.MARKDOWN)
                        db.log_admin_action(user.id, 'block_user', 'user', str(target_id), "Blocked user")
                    else:
                        await update.message.reply_text(f"❌ User `{target_id}` tidak ditemukan.", parse_mode=ParseMode.MARKDOWN)
            
            elif action == 'unblock':
                if db.unblock_user(target_id):
                    await update.message.reply_text(f"✅ User `{target_id}` telah dibuka blokirnya.", parse_mode=ParseMode.MARKDOWN)
                    db.log_admin_action(user.id, 'unblock_user', 'user', str(target_id), "Unblocked user")
                else:
                    await update.message.reply_text(f"❌ User `{target_id}` tidak ditemukan.", parse_mode=ParseMode.MARKDOWN)
            
            elif action == 'ban':
                if target_id in SUPER_ADMINS:
                    await update.message.reply_text("❌ Tidak bisa mem-ban super admin!")
                else:
                    context.user_data['ban_target'] = target_id
                    context.user_data['admin_action'] = 'ban_reason'
                    await update.message.reply_text(
                        f"📝 Masukkan alasan ban untuk user `{target_id}`:",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return
            
            del context.user_data['admin_action']
        
        except ValueError:
            await update.message.reply_text("❌ ID user harus berupa angka!")
        
        return
    
    # ===== ADMIN ADD FLOW =====
    if 'admin_step' in context.user_data:
        step = context.user_data['admin_step']
        
        if text.lower() == 'batal':
            del context.user_data['admin_step']
            await update.message.reply_text("✅ Operasi dibatalkan.")
            return
        
        if step == 'waiting_id':
            try:
                target_id = int(text)
                context.user_data['admin_target'] = target_id
                context.user_data['admin_step'] = 'confirm_add'
                
                user_data = db.get_user(target_id)
                if user_data:
                    name = user_data['first_name']
                    username = f"(@{user_data['username']})" if user_data['username'] else ""
                    info = f"{name} {username}"
                else:
                    info = f"User ID {target_id} (belum pernah interact)"
                
                await update.message.reply_text(
                    f"📋 *KONFIRMASI*\n\n"
                    f"Jadikan {info} sebagai admin?\n\n"
                    f"Ketik *ya* untuk konfirmasi, atau *tidak* untuk batal.",
                    parse_mode=ParseMode.MARKDOWN
                )
            except ValueError:
                await update.message.reply_text("❌ User ID harus berupa angka!")
        
        elif step == 'confirm_add':
            if text.lower() == 'ya':
                target_id = context.user_data['admin_target']
                
                if db.add_admin(target_id, user.id):
                    await update.message.reply_text(f"✅ User `{target_id}` sekarang adalah admin!", parse_mode=ParseMode.MARKDOWN)
                    db.log_admin_action(user.id, 'add_admin', 'user', str(target_id), "Added as admin")
                else:
                    await update.message.reply_text("❌ Gagal menambahkan admin.")
            else:
                await update.message.reply_text("✅ Penambahan admin dibatalkan.")
            
            del context.user_data['admin_step']
        
        elif step == 'edit_id':
            try:
                target_id = int(text)
                
                if target_id in SUPER_ADMINS:
                    await update.message.reply_text("❌ Tidak bisa mengedit super admin!")
                    del context.user_data['admin_step']
                    return
                
                # Get current permissions
                perms = db.get_admin_permissions(target_id)
                
                context.user_data['edit_admin_id'] = target_id
                context.user_data['admin_step'] = 'edit_permissions'
                
                perm_text = (
                    f"✏️ *EDIT PERMISSIONS ADMIN `{target_id}`*\n\n"
                    f"Permissions saat ini:\n"
                    f"• Manage Users: {'✅' if perms.get('can_manage_users') else '❌'}\n"
                    f"• Manage Posts: {'✅' if perms.get('can_manage_posts') else '❌'}\n"
                    f"• Broadcast: {'✅' if perms.get('can_broadcast') else '❌'}\n"
                    f"• View Stats: {'✅' if perms.get('can_view_stats') else '❌'}\n\n"
                    f"Masukkan permissions baru dalam format:\n"
                    f"users,posts,broadcast,stats\n"
                    f"Contoh: 1,1,0,1 (1=ya, 0=tidak)"
                )
                
                await update.message.reply_text(perm_text, parse_mode=ParseMode.MARKDOWN)
                
            except ValueError:
                await update.message.reply_text("❌ User ID harus berupa angka!")
        
        elif step == 'edit_permissions':
            try:
                parts = text.split(',')
                if len(parts) != 4:
                    await update.message.reply_text("❌ Format salah! Gunakan: 1,1,0,1")
                    return
                
                permissions = {
                    'can_manage_users': bool(int(parts[0])),
                    'can_manage_posts': bool(int(parts[1])),
                    'can_broadcast': bool(int(parts[2])),
                    'can_view_stats': bool(int(parts[3]))
                }
                
                target_id = context.user_data['edit_admin_id']
                
                if db.update_admin_permissions(target_id, user.id, permissions):
                    await update.message.reply_text(f"✅ Permissions admin `{target_id}` telah diupdate.", parse_mode=ParseMode.MARKDOWN)
                    db.log_admin_action(user.id, 'edit_admin', 'user', str(target_id), f"Updated permissions: {permissions}")
                else:
                    await update.message.reply_text("❌ Gagal mengupdate permissions.")
                
                del context.user_data['admin_step']
                del context.user_data['edit_admin_id']
                
            except:
                await update.message.reply_text("❌ Format salah! Gunakan: 1,1,0,1")
        
        elif step == 'remove_id':
            try:
                target_id = int(text)
                
                if target_id in SUPER_ADMINS:
                    await update.message.reply_text("❌ Tidak bisa menghapus super admin!")
                    del context.user_data['admin_step']
                    return
                
                if db.remove_admin(target_id, user.id):
                    await update.message.reply_text(f"✅ Admin `{target_id}` telah dihapus.", parse_mode=ParseMode.MARKDOWN)
                    db.log_admin_action(user.id, 'remove_admin', 'user', str(target_id), "Removed admin")
                else:
                    await update.message.reply_text(f"❌ Gagal menghapus admin `{target_id}`", parse_mode=ParseMode.MARKDOWN)
                
                del context.user_data['admin_step']
            except ValueError:
                await update.message.reply_text("❌ User ID harus berupa angka!")
        
        return

# ==================== WELCOME NEW MEMBER ====================

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome new channel members"""
    if not update.channel_post or not update.channel_post.new_chat_members:
        return
    
    message = update.channel_post
    chat = update.effective_chat
    
    if chat.id != CHANNEL_ID:
        return
    
    if not db.get_setting_with_type('welcome_enabled', True):
        return
    
    logger.info(f"🎉 New member detected in channel!")
    
    for new_member in message.new_chat_members:
        if new_member.is_bot:
            continue
        
        db.add_or_update_user(new_member)
        
        mention = f"[{new_member.first_name}](tg://user?id={new_member.id})"
        
        welcome_text = (
            f"🎉 *SELAMAT DATANG* 🎉\n\n"
            f"Halo {mention}!\n"
            f"Selamat bergabung di *{db.get_setting('bot_name')} Official Channel*!\n\n"
            f"📌 *Link Penting:*\n"
            f"• [🤖 BOT OFFICIAL]({config.get('urls.bot_official')})\n"
            f"• [🟢 WA KLAIM BONUS]({config.get('urls.claim')})\n"
            f"• [📢 CHANNEL WA]({config.get('urls.channel_wa')})\n"
            f"• [📢 CHANNEL TG]({config.get('urls.channel_tg')})\n\n"
            f"🔥 *GasPoll!* 🔥"
        )
        
        try:
            await context.bot.send_message(
                chat_id=chat.id,
                text=welcome_text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
            logger.info(f"✅ Welcome sent for {new_member.first_name}")
        except Exception as e:
            logger.error(f"❌ Failed to send welcome: {e}")

# ==================== TEST CHANNEL ====================

async def test_channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test channel connection"""
    user = update.effective_user
    db.add_or_update_user(user)
    
    try:
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text="🧪 *TEST BOT*\n\nBot aktif dan berjalan normal!",
            parse_mode=ParseMode.MARKDOWN
        )
        await update.message.reply_text("✅ Pesan test terkirim ke channel!")
    except Exception as e:
        await update.message.reply_text(f"❌ Gagal: {e}")

# ==================== JOB QUEUE ====================

async def check_auto_posts_job(context: ContextTypes.DEFAULT_TYPE):
    """Job to check and send auto posts"""
    await scheduler.check_and_send_posts(context)

async def check_scheduled_broadcasts_job(context: ContextTypes.DEFAULT_TYPE):
    """Job to check scheduled broadcasts"""
    pending = db.get_pending_broadcasts()
    
    for broadcast in pending:
        asyncio.create_task(
            broadcast_manager.send_broadcast(
                context,
                broadcast_id=broadcast['broadcast_id'],
                message_text=broadcast['message_text'],
                message_type=broadcast['message_type'],
                file_id=broadcast['file_id'],
                caption=broadcast['caption'],
                buttons=json.loads(broadcast['buttons']) if broadcast['buttons'] else None,
                filter_criteria=json.loads(broadcast['filter_criteria']) if broadcast['filter_criteria'] else None
            )
        )

async def auto_backup_job(context: ContextTypes.DEFAULT_TYPE):
    """Auto backup database"""
    if db.get_setting_with_type('auto_backup_enabled', True):
        db.backup_database()
        logger.info("💾 Auto backup completed")

# ==================== ERROR HANDLER ====================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"❌ ERROR: {context.error}")
    
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ Terjadi kesalahan. Silakan coba lagi nanti."
            )
    except:
        pass

# ==================== POST INIT ====================

async def post_init(application: Application):
    """Post initialization function"""
    logger.info("=" * 80)
    logger.info("🤖 BOT BOLAPELANGI 2 ULTIMATE PRO v3.0 READY!")
    logger.info("=" * 80)
    
    try:
        bot_info = await application.bot.get_me()
        logger.info(f"✅ Bot: @{bot_info.username}")
        logger.info(f"✅ Channel ID: {CHANNEL_ID}")
        logger.info(f"✅ Database: {DATABASE_FILE}")
        
        # Create required folders
        os.makedirs('data', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        os.makedirs('backups', exist_ok=True)
        logger.info("✅ Created required folders")
        
        # Set bot commands
        commands = [
            BotCommand("start", "Mulai bot"),
            BotCommand("help", "Bantuan"),
            BotCommand("info", "Info akun"),
            BotCommand("promo", "Lihat promo"),
            BotCommand("stats", "Statistik bot"),
        ]
        
        if db.is_super_admin(bot_info.id):
            commands.extend([
                BotCommand("admin", "Panel admin"),
                BotCommand("users", "Daftar user"),
                BotCommand("broadcast", "Kirim broadcast"),
                BotCommand("posts", "Kelola auto post"),
                BotCommand("admins", "Kelola admin"),
                BotCommand("settings", "Pengaturan"),
                BotCommand("backup", "Backup database"),
            ])
        
        await application.bot.set_my_commands(commands)
        logger.info("✅ Bot commands set")
        
        # Setup jobs
        job_queue = application.job_queue
        if job_queue:
            # Auto post check every minute
            job_queue.run_repeating(check_auto_posts_job, interval=60, first=10)
            
            # Scheduled broadcasts check every 5 minutes
            job_queue.run_repeating(check_scheduled_broadcasts_job, interval=300, first=30)
            
            # Auto backup every 24 hours
            job_queue.run_repeating(auto_backup_job, interval=86400, first=3600)
            
            logger.info("✅ Jobs scheduled")
        
        # Send startup message to channel
        try:
            await application.bot.send_message(
                chat_id=CHANNEL_ID,
                text="🤖 *Bot Ultimate Pro v3.0 Aktif*\n\n✅ Sistem auto post & broadcast siap!",
                parse_mode=ParseMode.MARKDOWN
            )
            logger.info("✅ Startup message sent to channel")
        except Exception as e:
            logger.error(f"❌ Cannot send to channel: {e}")
        
        # Log stats
        user_stats = db.get_user_count()
        logger.info(f"✅ Total users: {user_stats['total']}")
        logger.info(f"✅ Total admins: {len(db.get_all_admins())}")
        logger.info(f"✅ Total auto posts: {len(db.get_all_posts())}")
        
    except Exception as e:
        logger.error(f"❌ Post init error: {e}")

# ==================== MAIN FUNCTION ====================

def main():
    """Main function"""
    
    print("=" * 80)
    print("🤖 BOT BOLAPELANGI 2 - ULTIMATE PRO v3.0")
    print("=" * 80)
    print("🔧 FITUR SUPER LENGKAP:")
    print("   ✅ Auto Welcome Member")
    print("   ✅ Auto Post Terjadwal")
    print("   ✅ Broadcast System with Queue")
    print("   ✅ Database SQLite dengan Backup")
    print("   ✅ Admin Management with Permissions")
    print("   ✅ User Tracking & Analytics")
    print("   ✅ Super Admin Protection")
    print("   ✅ Statistics & Logs")
    print("   ✅ Message Templates")
    print("   ✅ Config via Telegram")
    print("   ✅ Auto Backup")
    print("=" * 80)
    
    if not BOT_TOKEN or len(BOT_TOKEN) < 40:
        print("❌ ERROR: BOT_TOKEN tidak valid!")
        sys.exit(1)
    
    print(f"✅ SUPER ADMIN: {SUPER_ADMINS}")
    
    try:
        application = (
            Application.builder()
            .token(BOT_TOKEN)
            .post_init(post_init)
            .concurrent_updates(True)
            .build()
        )
        print("✅ Application created")
    except Exception as e:
        print(f"❌ Failed: {e}")
        sys.exit(1)
    
    # Command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("info", info_command))
    application.add_handler(CommandHandler("promo", promo_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("test_channel", test_channel_command))
    
    # Admin commands
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("users", users_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("posts", posts_command))
    
    # Super admin commands
    application.add_handler(CommandHandler("admins", admins_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CommandHandler("set", set_command))
    application.add_handler(CommandHandler("backup", backup_command))
    
    # Callback handler
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Welcome handler
    application.add_handler(
        MessageHandler(
            filters.Chat(chat_id=CHANNEL_ID) & filters.StatusUpdate.NEW_CHAT_MEMBERS,
            welcome_new_member
        )
    )
    
    # Error handler
    application.add_error_handler(error_handler)
    
    print("=" * 80)
    print("📢 BOT RUNNING - ULTIMATE PRO v3.0")
    print("📢 Fitur: Auto Welcome | Auto Post | Broadcast | Admin Panel")
    print("📢 Database: SQLite dengan auto backup")
    print("📢 Super Admin: @Bolapelangi2 & @bolapelangi_2")
    print("=" * 80)
    sys.stdout.flush()
    
    # Start bot
    application.run_polling(
        allowed_updates=["message", "channel_post", "callback_query"],
        drop_pending_updates=True
    )

if __name__ == "__main__":
    main()
