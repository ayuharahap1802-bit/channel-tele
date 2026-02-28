"""
TELEGRAM BOT SUPER LENGKAP - BOLAPELANGI 2
VERSI: ULTIMATE PRO v3.0
Fitur: Auto Welcome | Auto Post Scheduler | Broadcast | Admin Panel | User Tracking | Full Config via Telegram
Created for: @bolapelangi2_bot
Author: Sistem Profesional
"""

# ==================== WEB SERVER UNTUK RAILWAY HEALTH CHECK ====================
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

# ==================== IMPORT LIBRARIES ====================
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
                'auto_backup_interval': 24
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

# ==================== TEKS PROMO DARI SCRIPT PERTAMA ====================

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
🤖 [BOT OFFICIAL](https://t.me/bolapelangi2_bot)
📈 [PREDIKSI JITU](https://bopel2.vip/ChannelWA-Jadwal-Prediksi)
📢 [CHANNEL WHATSAPP](https://bopel2.vip/Channel-Whatsapp)
📢 [CHANNEL TELEGRAM](https://bopel2.vip/Channel-Telegram)
🟢 [KLAIM BONUS](https://bopel2.link/wa)

📌 *Catatan:* 1x/hari, no IP sama, no safety bet
🚀 *GASPOLL TERUS BOSKU!
"""

# ==================== AUTO POST MANAGER DARI SCRIPT PERTAMA ====================

class AutoPostManager:
    """Manager untuk menyimpan dan mengelola jadwal auto post (dari script pertama)"""
    
    def __init__(self, filename="auto_posts.json"):
        self.filename = filename
        self.posts = self.load_posts()
        self.authorized_users = set()  # User yang diizinkan mengatur bot
        self.pending_input = {}  # Menyimpan state input user
    
    def load_posts(self) -> Dict:
        """Load jadwal dari file"""
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r') as f:
                    data = json.load(f)
                    # Konversi string jam ke format yang bisa diproses
                    for post_id, post in data.items():
                        if 'time' in post and isinstance(post['time'], str):
                            hour, minute = map(int, post['time'].split(':'))
                            post['time_obj'] = time(hour, minute)
                    logger.info(f"✅ Loaded {len(data)} jadwal dari file")
                    return data
            else:
                # Data default jika file tidak ada
                default_posts = {
                    "1": {
                        "id": "1",
                        "time": "08:00",
                        "time_obj": time(8, 0),
                        "text": "☀️ *SELAMAT PAGI* ☀️\n\nJangan lupa cek promo terbaru kami hari ini!",
                        "image_url": None,
                        "active": True
                    },
                    "2": {
                        "id": "2",
                        "time": "12:00",
                        "time_obj": time(12, 0),
                        "text": "⚽ *INFO SIANG* ⚽\n\nMasih bingung cari bettingan? Cek prediksi jitu kami!",
                        "image_url": None,
                        "active": True
                    },
                    "3": {
                        "id": "3",
                        "time": "19:00",
                        "time_obj": time(19, 0),
                        "text": PROMO_TEXT,
                        "image_url": "https://i.ibb.co/your-image/promo-banner.jpg",
                        "active": True
                    }
                }
                # Tambah time_obj ke default
                for post_id, post in default_posts.items():
                    if 'time' in post:
                        hour, minute = map(int, post['time'].split(':'))
                        post['time_obj'] = time(hour, minute)
                return default_posts
        except Exception as e:
            logger.error(f"❌ Gagal load jadwal: {e}")
            return {}
    
    def save_posts(self):
        """Simpan jadwal ke file"""
        try:
            # Hapus time_obj sebelum save ke JSON
            save_data = {}
            for post_id, post in self.posts.items():
                save_data[post_id] = {k: v for k, v in post.items() if k != 'time_obj'}
            with open(self.filename, 'w') as f:
                json.dump(save_data, f, indent=2)
            logger.info(f"✅ Saved {len(self.posts)} jadwal ke file")
        except Exception as e:
            logger.error(f"❌ Gagal save jadwal: {e}")
    
    def add_post(self, post_id: str, time_str: str, text: str, image_url: str = None):
        """Tambah jadwal baru"""
        hour, minute = map(int, time_str.split(':'))
        self.posts[post_id] = {
            "id": post_id,
            "time": time_str,
            "time_obj": time(hour, minute),
            "text": text,
            "image_url": image_url,
            "active": True
        }
        self.save_posts()
    
    def update_post(self, post_id: str, **kwargs):
        """Update jadwal"""
        if post_id in self.posts:
            if 'time' in kwargs:
                hour, minute = map(int, kwargs['time'].split(':'))
                kwargs['time_obj'] = time(hour, minute)
            self.posts[post_id].update(kwargs)
            self.save_posts()
            return True
        return False
    
    def delete_post(self, post_id: str):
        """Hapus jadwal"""
        if post_id in self.posts:
            del self.posts[post_id]
            self.save_posts()
            return True
        return False
    
    def get_next_run_time(self) -> Optional[datetime]:
        """Dapatkan waktu jadwal berikutnya yang akan dijalankan"""
        now = datetime.now()
        today = now.date()
        
        # Cari jadwal aktif
        next_run = None
        for post in self.posts.values():
            if not post.get('active', True):
                continue
            
            post_time = post['time_obj']
            run_datetime = datetime.combine(today, post_time)
            
            # Jika waktu sudah lewat hari ini, jadwalkan untuk besok
            if run_datetime <= now:
                run_datetime += timedelta(days=1)
            
            if next_run is None or run_datetime < next_run:
                next_run = run_datetime
        
        return next_run
    
    def get_posts_due_now(self) -> List[Dict]:
        """Dapatkan semua jadwal yang harus dijalankan sekarang"""
        now = datetime.now()
        current_time = now.time()
        due_posts = []
        
        for post in self.posts.values():
            if not post.get('active', True):
                continue
            
            # Cek apakah waktunya cocok (dalam 1 menit ke depan)
            post_time = post['time_obj']
            time_diff = abs(datetime.combine(now.date(), post_time) - datetime.combine(now.date(), current_time))
            if time_diff.total_seconds() < 60:  # Toleransi 1 menit
                due_posts.append(post)
        
        return due_posts

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
            
            # Auto posts table (terintegrasi dengan database SQLite)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS auto_posts_sql (
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
            
            backup_conn = sqlite3.connect(backup_file)
            with self.get_connection() as conn:
                backup_conn.backup(conn)
            backup_conn.close()
            
            logger.info(f"✅ Database restored from {backup_file}")
            return True
        except Exception as e:
            logger.error(f"❌ Restore failed: {e}")
            return False
    
    # ========== USER MANAGEMENT ==========
    
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
            
            cursor.execute('SELECT COUNT(*) as total FROM users')
            total = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) as today FROM users WHERE date(joined_date) = date("now")')
            today = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) as week FROM users WHERE joined_date >= datetime("now", "-7 days")')
            week = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) as month FROM users WHERE joined_date >= datetime("now", "-30 days")')
            month = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) as active_24h FROM users WHERE last_active > datetime("now", "-1 day")')
            active_24h = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) as active_week FROM users WHERE last_active > datetime("now", "-7 days")')
            active_week = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) as blocked FROM users WHERE is_blocked = 1')
            blocked = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) as banned FROM users WHERE is_banned = 1')
            banned = cursor.fetchone()[0]
            
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
        """Ban a user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET is_banned = 1, ban_reason = ?, is_blocked = 1 WHERE user_id = ?', (reason, user_id))
            return cursor.rowcount > 0
    
    # ========== ADMIN MANAGEMENT ==========
    
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
            
            user_data = self.get_user(user_id)
            username = user_data['username'] if user_data else None
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
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
                
                self.log_admin_action(added_by, 'add_admin', 'user', str(user_id), "Added as admin")
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
                self.log_admin_action(removed_by, 'remove_admin', 'user', str(user_id), "Removed admin")
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"❌ Failed to remove admin {user_id}: {e}")
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
    
    # ========== BROADCAST MANAGEMENT ==========
    
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
    
    def update_broadcast_status(self, broadcast_id: int, status: str, success: int = 0, failed: int = 0):
        """Update broadcast status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE broadcast_messages 
                SET status = ?, success_count = success_count + ?, 
                    failed_count = failed_count + ?, sent_time = CURRENT_TIMESTAMP
                WHERE broadcast_id = ?
            ''', (status, success, failed, broadcast_id))
    
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
                    config.set(key, value)
                    return True
                return False
        except Exception as e:
            logger.error(f"❌ Failed to update setting {key}: {e}")
            return False
    
    def get_all_settings(self) -> List[Dict]:
        """Get all settings"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
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

# ==================== INISIALISASI ====================

db = DatabaseManager()
post_manager = AutoPostManager()  # Dari script pertama

# ==================== LOAD JSON DATA ====================

def load_initial_data():
    """Load initial data from JSON files"""
    try:
        data_folder = 'data'
        
        # Load auto_posts.json ke post_manager
        posts_path = os.path.join(data_folder, 'auto_posts.json')
        if os.path.exists(posts_path):
            with open(posts_path, 'r') as f:
                posts = json.load(f)
            
            if posts:
                for i, post in enumerate(posts, 1):
                    post_id = str(i)
                    if post_id not in post_manager.posts:
                        post_manager.add_post(
                            post_id=post_id,
                            time_str=post.get('time'),
                            text=post.get('text'),
                            image_url=post.get('image_url')
                        )
                logger.info(f"✅ Loaded {len(posts)} auto posts ke post_manager")
        
        # Load templates
        templates_path = os.path.join(data_folder, 'broadcast_templates.json')
        if os.path.exists(templates_path):
            logger.info(f"✅ Broadcast templates available")
        
        # Load settings
        settings_path = os.path.join(data_folder, 'bot_settings.json')
        if os.path.exists(settings_path):
            logger.info(f"✅ Bot settings available")
            
    except Exception as e:
        logger.error(f"❌ Failed to load initial data: {e}")

load_initial_data()

# ==================== AUTO POST SCHEDULER (MENGGABUNGKAN KEDUA SCRIPT) ====================

class AutoPostScheduler:
    """Manager untuk auto posting terjadwal (gabungan dari kedua script)"""
    
    def __init__(self):
        self.running = True
        logger.info("✅ AutoPostScheduler initialized")
    
    async def check_and_send_posts(self, context: ContextTypes.DEFAULT_TYPE):
        """Cek dan kirim postingan yang waktunya sudah tiba"""
        if not db.get_setting_with_type('auto_post_enabled', True):
            return
        
        # Gunakan post_manager dari script pertama
        due_posts = post_manager.get_posts_due_now()
        
        if due_posts:
            logger.info(f"⏰ Menemukan {len(due_posts)} jadwal yang harus dikirim")
            for post in due_posts:
                await self.send_post(context, post)
    
    async def send_post(self, context: ContextTypes.DEFAULT_TYPE, post: Dict):
        """Kirim postingan ke channel"""
        try:
            logger.info(f"📢 Mengirim auto post jadwal {post.get('id')} - {post.get('time')}")
            
            # Buat keyboard default untuk promo (dari script pertama)
            keyboard = [
                [InlineKeyboardButton("🤖 BOT OFFICIAL", url="https://t.me/bolapelangi2_bot")],
                [InlineKeyboardButton("📈 PREDIKSI JITU", url="https://bopel2.vip/ChannelWA-Jadwal-Prediksi")],
                [InlineKeyboardButton("📢 CHANNEL WA", url="https://bopel2.vip/Channel-Whatsapp")],
                [InlineKeyboardButton("📢 CHANNEL TG", url="https://bopel2.vip/Channel-Telegram")],
                [InlineKeyboardButton("🟢 KLAIM BONUS", url="https://bopel2.link/wa")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Kirim dengan gambar jika ada
            if post.get('image_url'):
                try:
                    await context.bot.send_photo(
                        chat_id=CHANNEL_ID,
                        photo=post['image_url'],
                        caption=post['text'],
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=reply_markup
                    )
                    logger.info(f"✅ Auto post {post.get('id')} terkirim dengan gambar")
                except Exception as e:
                    logger.warning(f"⚠️ Gagal kirim gambar: {e}, kirim teks saja")
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
                logger.info(f"✅ Auto post {post.get('id')} terkirim")
            
            # Jadwalkan pengiriman berikutnya
            await self.schedule_next_run(context)
            
        except Exception as e:
            logger.error(f"❌ Gagal auto post: {e}")
    
    async def schedule_next_run(self, context: ContextTypes.DEFAULT_TYPE):
        """Jadwalkan pengecekan berikutnya (dari script pertama)"""
        next_run = post_manager.get_next_run_time()
        
        if next_run:
            # Hapus job yang sudah ada
            current_jobs = context.job_queue.get_jobs_by_name('check_posts')
            for job in current_jobs:
                job.schedule_removal()
            
            # Hitung delay sampai waktu berikutnya
            now = datetime.now()
            delay = (next_run - now).total_seconds()
            
            # Jadwalkan job baru
            context.job_queue.run_once(
                self.check_and_send_posts,
                when=max(delay, 1),  # Minimal 1 detik
                name='check_posts'
            )
            logger.info(f"📅 Next check scheduled at {next_run.strftime('%Y-%m-%d %H:%M:%S')} (in {delay/60:.1f} minutes)")
        else:
            logger.warning("⚠️ Tidak ada jadwal aktif")

scheduler = AutoPostScheduler()

# ==================== BROADCAST MANAGER ====================

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
        
        users = db.get_all_users() if not filter_criteria else self._filter_users(filter_criteria)
        total_users = len(users)
        
        if total_users == 0:
            logger.warning("⚠️ No users to broadcast")
            return
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE broadcast_messages 
                SET total_recipients = ?, status = 'sending' 
                WHERE broadcast_id = ?
            ''', (total_users, broadcast_id))
        
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
        
        success = 0
        failed = 0
        delay = db.get_setting_with_type('broadcast_delay', 1)
        
        self.is_sending = True
        self.current_broadcast = broadcast_id
        
        for user in users:
            user_id = user['user_id']
            
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
                
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO broadcast_recipients (broadcast_id, user_id, sent_status, sent_time)
                        VALUES (?, ?, 'success', CURRENT_TIMESTAMP)
                    ''', (broadcast_id, user_id))
                
            except Exception as e:
                failed += 1
                logger.error(f"❌ Failed to send to {user_id}: {e}")
                
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO broadcast_recipients (broadcast_id, user_id, sent_status, error_message)
                        VALUES (?, ?, 'failed', ?)
                    ''', (broadcast_id, user_id, str(e)[:200]))
            
            await asyncio.sleep(delay)
        
        db.update_broadcast_status(broadcast_id, 'sent', success, failed)
        
        self.is_sending = False
        self.current_broadcast = None
        
        logger.info(f"✅ Broadcast {broadcast_id} completed: {success} success, {failed} failed")
        return {'success': success, 'failed': failed, 'total': total_users}
    
    def _filter_users(self, criteria: Dict) -> List[Dict]:
        """Filter users based on criteria"""
        conditions = ["1=1"]
        params = []
        
        if criteria.get('active_last_days'):
            conditions.append("last_active > datetime('now', '-? days')")
            params.append(criteria['active_last_days'])
        
        if criteria.get('language'):
            conditions.append("language_code = ?")
            params.append(criteria['language'])
        
        if criteria.get('not_blocked'):
            conditions.append("is_blocked = 0")
        
        if criteria.get('not_banned'):
            conditions.append("is_banned = 0")
        
        query = f"SELECT * FROM users WHERE {' AND '.join(conditions)} ORDER BY joined_date DESC"
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

broadcast_manager = BroadcastManager()

# ==================== DECORATORS ====================

def role_required(min_role: UserRole = UserRole.ADMIN):
    """Decorator for role-based access control"""
    def decorator(func):
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user = update.effective_user
            user_role = db.get_user_role(user.id)
            
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
    """Handle /start command (gabungan dari kedua script)"""
    user = update.effective_user
    start_time = datetime.now()
    
    db.add_or_update_user(user)
    
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
    
    # Teks dari script pertama
    text = (
        f"Halo *{user.first_name}*! 👋\n\n"
        f"Selamat datang di *BOLAPELANGI 2 Bot*!\n\n"
        f"🤖 *Menu Utama:*\n"
        f"• Gunakan button di bawah untuk akses cepat\n"
        f"• Klik button LIHAT PROMO untuk promo terbaru\n"
        f"• Ketik /help untuk bantuan\n\n"
        f"🔥 *GasPoll!* 🔥"
    )
    
    # Button dari script pertama
    keyboard = [
        [
            InlineKeyboardButton("🔐 LOGIN", callback_data='login'),
            InlineKeyboardButton("📝 DAFTAR", callback_data='daftar'),
        ],
        [
            InlineKeyboardButton("🎁 CLAIM EVENT", callback_data='claim'),
        ],
        [
            InlineKeyboardButton("📢 LIHAT PROMO", callback_data='promo'),
        ]
    ]
    
    # Tambah button admin jika user terauthorisasi (dari script pertama)
    if user.id in post_manager.authorized_users:
        keyboard.append([InlineKeyboardButton("⚙️ ADMIN PANEL", callback_data='admin_back')])
    
    # Tambah button admin dari script kedua
    if db.is_admin(user.id):
        # Cek apakah sudah ada button admin, jika belum tambahkan
        has_admin = any(btn[0].callback_data == 'admin_dashboard' for row in keyboard for btn in row if hasattr(btn[0], 'callback_data'))
        if not has_admin:
            keyboard.append([InlineKeyboardButton("⚙️ PANEL ADMIN", callback_data='admin_dashboard')])
    
    if db.is_super_admin(user.id):
        has_super = any(btn[0].callback_data == 'super_admin_dashboard' for row in keyboard for btn in row if hasattr(btn[0], 'callback_data'))
        if not has_super:
            keyboard.append([InlineKeyboardButton("⭐ SUPER ADMIN PANEL", callback_data='super_admin_dashboard')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
        reply_markup=reply_markup
    )
    
    response_time = int((datetime.now() - start_time).total_seconds() * 1000)
    db.log_interaction(user.id, '/start', response_time=response_time)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command (gabungan)"""
    user = update.effective_user
    db.add_or_update_user(user)
    
    role = db.get_user_role(user.id)
    
    # Base help text
    help_text = (
        "📚 *BANTUAN BOT*\n\n"
        "✨ *Perintah untuk Semua User:*\n"
        "• /start - Mulai bot\n"
        "• /promo - Lihat promo terbaru\n"
        "• /help - Tampilkan bantuan ini\n"
        "• /info - Info akun Anda\n"
        "• /stats - Statistik bot\n"
    )
    
    # Admin commands dari script pertama
    if user.id in post_manager.authorized_users:
        help_text += (
            "\n👑 *Perintah Admin (Auto Post):*\n"
            "• /list_jadwal - Lihat semua jadwal\n"
            "• /tambah_jadwal - Tambah jadwal baru\n"
            "• /edit_jadwal [id] - Edit jadwal\n"
            "• /hapus_jadwal [id] - Hapus jadwal\n"
            "• /aktifkan_jadwal [id] - Aktifkan jadwal\n"
            "• /nonaktifkan_jadwal [id] - Nonaktifkan jadwal\n"
        )
    
    # Admin commands dari script kedua
    if role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        help_text += (
            "\n👑 *Perintah Admin Panel:*\n"
            "• /admin - Dashboard admin\n"
            "• /users - Daftar user\n"
            "• /broadcast - Kirim broadcast\n"
            "• /posts - Kelola auto post (SQLite)\n"
        )
    
    if role == UserRole.SUPER_ADMIN:
        help_text += (
            "\n⭐ *Perintah Super Admin:*\n"
            "• /admins - Kelola admin\n"
            "• /settings - Pengaturan bot\n"
            "• /set [key] [value] - Ubah pengaturan\n"
            "• /backup - Backup database\n"
            "• /block [user_id] - Blokir user\n"
            "• /unblock [user_id] - Buka blokir\n"
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
    
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    db.log_interaction(user.id, '/info')

async def promo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /promo command - Tampilkan promo dengan gambar (dari script pertama)"""
    user = update.effective_user
    
    db.add_or_update_user(user)
    db.log_interaction(user.id, '/promo')
    
    logger.info(f"🎁 /promo dari {user.first_name} (ID: {user.id})")
    
    # Buat button untuk link (dari script pertama)
    keyboard = [
        [InlineKeyboardButton("🤖 BOT OFFICIAL", url="https://t.me/bolapelangi2_bot")],
        [InlineKeyboardButton("📈 PREDIKSI JITU", url="https://bopel2.vip/ChannelWA-Jadwal-Prediksi")],
        [InlineKeyboardButton("📢 CHANNEL WA", url="https://bopel2.vip/Channel-Whatsapp")],
        [InlineKeyboardButton("📢 CHANNEL TG", url="https://bopel2.vip/Channel-Telegram")],
        [InlineKeyboardButton("🟢 KLAIM BONUS", url="https://bopel2.link/wa")],
        [InlineKeyboardButton("🔙 KEMBALI KE MENU", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Coba ambil gambar dari jadwal pertama jika ada
    image_url = None
    for post in post_manager.posts.values():
        if post.get('image_url'):
            image_url = post['image_url']
            break
    
    if not image_url:
        image_url = config.get('images.default_promo', "https://i.ibb.co/your-image/promo-banner.jpg")
    
    # Coba kirim dengan gambar
    try:
        await update.message.reply_photo(
            photo=image_url,
            caption=PROMO_TEXT,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        logger.info("✅ Promo dengan gambar terkirim")
    except Exception as e:
        logger.warning(f"⚠️ Gagal kirim gambar: {e}, kirim teks saja")
        await update.message.reply_text(
            text=PROMO_TEXT,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=reply_markup
        )

# ==================== ADMIN COMMANDS DARI SCRIPT PERTAMA ====================

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command untuk mengatur auto post - HANYA UNTUK ADMIN TERTENTU (dari script pertama)"""
    user = update.effective_user
    
    logger.info(f"👑 /admin digunakan oleh {user.first_name} (ID: {user.id})")
    
    # Tambahkan user ke authorized list
    post_manager.authorized_users.add(user.id)
    
    text = (
        "🔧 *PANEL ADMIN AUTO POST*\n\n"
        "Kelola jadwal posting otomatis ke channel.\n\n"
        "📋 *Menu:*\n"
        "• /list_jadwal - Lihat semua jadwal\n"
        "• /tambah_jadwal - Tambah jadwal baru\n"
        "• /edit_jadwal [id] - Edit jadwal\n"
        "• /hapus_jadwal [id] - Hapus jadwal\n"
        "• /aktifkan_jadwal [id] - Aktifkan jadwal\n"
        "• /nonaktifkan_jadwal [id] - Nonaktifkan jadwal\n\n"
        "Atau gunakan tombol di bawah:"
    )
    
    keyboard = [
        [InlineKeyboardButton("📋 LIST JADWAL", callback_data='admin_list')],
        [InlineKeyboardButton("➕ TAMBAH JADWAL", callback_data='admin_add')],
        [InlineKeyboardButton("🔄 CEK JADWAL BERIKUTNYA", callback_data='admin_next')],
        [InlineKeyboardButton("🔙 KEMBALI KE MENU", callback_data='menu_utama')]
    ]
    
    await update.message.reply_text(
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def list_jadwal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tampilkan semua jadwal auto post (dari script pertama)"""
    user = update.effective_user
    
    if user.id not in post_manager.authorized_users:
        await update.message.reply_text("❌ Anda tidak diizinkan menggunakan perintah ini.")
        return
    
    if not post_manager.posts:
        await update.message.reply_text("📋 Belum ada jadwal tersedia.")
        return
    
    text = "📋 *DAFTAR JADWAL AUTO POST*\n\n"
    
    for post_id, post in post_manager.posts.items():
        status = "✅ AKTIF" if post.get('active', True) else "❌ NONAKTIF"
        has_image = "📷" if post.get('image_url') else "📝"
        text += f"{has_image} *ID {post_id}:* {post.get('time')} - {status}\n"
        preview = post.get('text', '')[:50] + ('...' if len(post.get('text', '')) > 50 else '')
        text += f"   `{preview}`\n\n"
    
    text += "\nGunakan /edit_jadwal [id] untuk mengedit."
    
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def tambah_jadwal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mulai proses tambah jadwal (dari script pertama)"""
    user = update.effective_user
    
    if user.id not in post_manager.authorized_users:
        await update.message.reply_text("❌ Anda tidak diizinkan menggunakan perintah ini.")
        return
    
    post_manager.pending_input[user.id] = {
        'action': 'add',
        'step': 'time'
    }
    
    text = (
        "🕐 *TAMBAH JADWAL BARU - LANGKAH 1/4*\n\n"
        "Masukkan waktu pengiriman dalam format *HH:MM* (24 jam)\n"
        "Contoh: `14:30` untuk jam 2:30 sore\n\n"
        "Ketik *batal* untuk membatalkan."
    )
    
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def edit_jadwal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mulai proses edit jadwal (dari script pertama)"""
    user = update.effective_user
    
    if user.id not in post_manager.authorized_users:
        await update.message.reply_text("❌ Anda tidak diizinkan menggunakan perintah ini.")
        return
    
    args = context.args
    if not args:
        await update.message.reply_text("❌ Gunakan: /edit_jadwal [id]\nContoh: /edit_jadwal 1")
        return
    
    post_id = args[0]
    if post_id not in post_manager.posts:
        await update.message.reply_text(f"❌ Jadwal dengan ID {post_id} tidak ditemukan.")
        return
    
    post_manager.pending_input[user.id] = {
        'action': 'edit',
        'post_id': post_id,
        'step': 'field'
    }
    
    post = post_manager.posts[post_id]
    text = (
        f"✏️ *EDIT JADWAL ID {post_id}*\n\n"
        f"Waktu: {post.get('time')}\n"
        f"Status: {'Aktif' if post.get('active', True) else 'Nonaktif'}\n"
        f"Gambar: {'Ada' if post.get('image_url') else 'Tidak ada'}\n\n"
        f"Preview teks:\n{post.get('text', '')[:100]}{'...' if len(post.get('text', '')) > 100 else ''}\n\n"
        f"Pilih yang ingin diedit:"
    )
    
    keyboard = [
        [InlineKeyboardButton("🕐 WAKTU", callback_data=f'edit_field_time_{post_id}')],
        [InlineKeyboardButton("📝 TEKS", callback_data=f'edit_field_text_{post_id}')],
        [InlineKeyboardButton("📷 GAMBAR", callback_data=f'edit_field_image_{post_id}')],
        [InlineKeyboardButton("✅ AKTIF/NONAKTIF", callback_data=f'edit_field_active_{post_id}')],
        [InlineKeyboardButton("🔙 BATAL", callback_data='admin_list')]
    ]
    
    await update.message.reply_text(
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def hapus_jadwal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hapus jadwal (dari script pertama)"""
    user = update.effective_user
    
    if user.id not in post_manager.authorized_users:
        await update.message.reply_text("❌ Anda tidak diizinkan menggunakan perintah ini.")
        return
    
    args = context.args
    if not args:
        await update.message.reply_text("❌ Gunakan: /hapus_jadwal [id]\nContoh: /hapus_jadwal 1")
        return
    
    post_id = args[0]
    if post_id not in post_manager.posts:
        await update.message.reply_text(f"❌ Jadwal dengan ID {post_id} tidak ditemukan.")
        return
    
    post_manager.pending_input[user.id] = {
        'action': 'delete',
        'post_id': post_id
    }
    
    post = post_manager.posts[post_id]
    text = (
        f"⚠️ *KONFIRMASI HAPUS*\n\n"
        f"Yakin ingin menghapus jadwal ID {post_id}?\n"
        f"Waktu: {post.get('time')}\n\n"
        f"Ketik *ya* untuk menghapus, atau *tidak* untuk membatalkan."
    )
    
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def aktifkan_jadwal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Aktifkan jadwal (dari script pertama)"""
    user = update.effective_user
    
    if user.id not in post_manager.authorized_users:
        await update.message.reply_text("❌ Anda tidak diizinkan menggunakan perintah ini.")
        return
    
    args = context.args
    if not args:
        await update.message.reply_text("❌ Gunakan: /aktifkan_jadwal [id]\nContoh: /aktifkan_jadwal 1")
        return
    
    post_id = args[0]
    if post_id not in post_manager.posts:
        await update.message.reply_text(f"❌ Jadwal dengan ID {post_id} tidak ditemukan.")
        return
    
    post_manager.update_post(post_id, active=True)
    await update.message.reply_text(f"✅ Jadwal ID {post_id} telah diaktifkan.")
    
    await scheduler.schedule_next_run(context)

async def nonaktifkan_jadwal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Nonaktifkan jadwal (dari script pertama)"""
    user = update.effective_user
    
    if user.id not in post_manager.authorized_users:
        await update.message.reply_text("❌ Anda tidak diizinkan menggunakan perintah ini.")
        return
    
    args = context.args
    if not args:
        await update.message.reply_text("❌ Gunakan: /nonaktifkan_jadwal [id]\nContoh: /nonaktifkan_jadwal 1")
        return
    
    post_id = args[0]
    if post_id not in post_manager.posts:
        await update.message.reply_text(f"❌ Jadwal dengan ID {post_id} tidak ditemukan.")
        return
    
    post_manager.update_post(post_id, active=False)
    await update.message.reply_text(f"✅ Jadwal ID {post_id} telah dinonaktifkan.")
    
    await scheduler.schedule_next_run(context)

# ==================== MESSAGE HANDLER UNTUK INPUT (dari script pertama) ====================

async def handle_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle input dari user (untuk proses tambah/edit)"""
    user = update.effective_user
    text = update.message.text
    
    if user.id not in post_manager.pending_input:
        return
    
    state = post_manager.pending_input[user.id]
    
    if text.lower() == 'batal':
        del post_manager.pending_input[user.id]
        await update.message.reply_text("✅ Proses dibatalkan.")
        return
    
    if state['action'] == 'add':
        await handle_add_input(update, context, state)
    elif state['action'] == 'edit':
        await handle_edit_input(update, context, state)
    elif state['action'] == 'delete':
        await handle_delete_input(update, context, state)

async def handle_add_input(update: Update, context: ContextTypes.DEFAULT_TYPE, state: Dict):
    """Handle input untuk tambah jadwal"""
    user = update.effective_user
    text = update.message.text
    
    if state['step'] == 'time':
        try:
            hour, minute = map(int, text.split(':'))
            if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                raise ValueError
            
            state['time'] = text
            state['step'] = 'text'
            
            await update.message.reply_text(
                "📝 *LANGKAH 2/4*\n\n"
                "Masukkan teks yang ingin dikirim.\n"
                "Gunakan format *Markdown* untuk bold/italic/link.\n\n"
                "Ketik *batal* untuk membatalkan.",
                parse_mode=ParseMode.MARKDOWN
            )
        except:
            await update.message.reply_text(
                "❌ Format waktu salah! Gunakan HH:MM (contoh: 14:30)\n"
                "Ketik *batal* untuk membatalkan.",
                parse_mode=ParseMode.MARKDOWN
            )
    
    elif state['step'] == 'text':
        state['text'] = text
        state['step'] = 'image'
        
        await update.message.reply_text(
            "📷 *LANGKAH 3/4*\n\n"
            "Masukkan URL gambar (opsional).\n"
            "Ketik *-* jika tidak pakai gambar.\n\n"
            "Ketik *batal* untuk membatalkan.",
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif state['step'] == 'image':
        image_url = None if text == '-' else text
        state['image_url'] = image_url
        state['step'] = 'confirm'
        
        confirm_text = (
            "🔍 *KONFIRMASI JADWAL BARU*\n\n"
            f"🕐 Waktu: {state['time']}\n"
            f"📷 Gambar: {'Ada' if image_url else 'Tidak ada'}\n\n"
            f"📝 Teks:\n{state['text']}\n\n"
            f"Ketik *simpan* untuk menyimpan, atau *batal* untuk membatalkan."
        )
        
        await update.message.reply_text(confirm_text, parse_mode=ParseMode.MARKDOWN)
    
    elif state['step'] == 'confirm':
        if text.lower() == 'simpan':
            new_id = str(len(post_manager.posts) + 1)
            while new_id in post_manager.posts:
                new_id = str(int(new_id) + 1)
            
            post_manager.add_post(
                post_id=new_id,
                time_str=state['time'],
                text=state['text'],
                image_url=state['image_url']
            )
            
            del post_manager.pending_input[user.id]
            await update.message.reply_text(f"✅ Jadwal ID {new_id} berhasil ditambahkan!")
            
            await scheduler.schedule_next_run(context)
        else:
            del post_manager.pending_input[user.id]
            await update.message.reply_text("❌ Proses dibatalkan.")

async def handle_edit_input(update: Update, context: ContextTypes.DEFAULT_TYPE, state: Dict):
    """Handle input untuk edit jadwal"""
    user = update.effective_user
    text = update.message.text
    post_id = state['post_id']
    
    if state['step'] == 'time':
        try:
            hour, minute = map(int, text.split(':'))
            if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                raise ValueError
            
            post_manager.update_post(post_id, time=text)
            del post_manager.pending_input[user.id]
            await update.message.reply_text(f"✅ Waktu jadwal ID {post_id} diupdate ke {text}")
            
            await scheduler.schedule_next_run(context)
        except:
            await update.message.reply_text("❌ Format waktu salah! Gunakan HH:MM")
    
    elif state['step'] == 'text':
        post_manager.update_post(post_id, text=text)
        del post_manager.pending_input[user.id]
        await update.message.reply_text(f"✅ Teks jadwal ID {post_id} telah diupdate")
    
    elif state['step'] == 'image':
        image_url = None if text == '-' else text
        post_manager.update_post(post_id, image_url=image_url)
        del post_manager.pending_input[user.id]
        await update.message.reply_text(f"✅ Gambar jadwal ID {post_id} telah diupdate")

async def handle_delete_input(update: Update, context: ContextTypes.DEFAULT_TYPE, state: Dict):
    """Handle input untuk hapus jadwal"""
    user = update.effective_user
    text = update.message.text.lower()
    post_id = state['post_id']
    
    if text == 'ya':
        post_manager.delete_post(post_id)
        del post_manager.pending_input[user.id]
        await update.message.reply_text(f"✅ Jadwal ID {post_id} telah dihapus")
        
        await scheduler.schedule_next_run(context)
    elif text == 'tidak':
        del post_manager.pending_input[user.id]
        await update.message.reply_text("✅ Penghapusan dibatalkan")
    else:
        await update.message.reply_text("❌ Ketik *ya* atau *tidak*", parse_mode=ParseMode.MARKDOWN)

# ==================== ADMIN DASHBOARD (dari script kedua) ====================

@role_required(UserRole.ADMIN)
async def admin_panel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin command - Dashboard admin (dari script kedua)"""
    user = update.effective_user
    role = db.get_user_role(user.id)
    
    user_stats = db.get_user_stats()
    posts = db.get_all_posts()
    active_posts = sum(1 for p in posts if p['is_active'])
    broadcast_stats = db.get_broadcast_stats()
    
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
        f"📅 *AUTO POST (SQLite)*\n"
        f"• Total Jadwal: {len(posts)}\n"
        f"• Jadwal Aktif: {active_posts}\n\n"
        f"📢 *BROADCAST*\n"
        f"• Total Broadcast: {broadcast_stats['total']}\n"
        f"• Terjadwal: {scheduled_broadcasts}\n"
        f"• Success Rate: {broadcast_stats['success_rate']:.1f}%\n\n"
        f"📋 *AKTIVITAS*\n"
        f"• Log Hari Ini: {today_logs}\n"
    )
    
    keyboard = []
    perms = db.get_admin_permissions(user.id) if role == UserRole.ADMIN else {}
    
    if role == UserRole.SUPER_ADMIN or perms.get('can_manage_users', True):
        keyboard.append([InlineKeyboardButton("👥 MANAJEMEN USER", callback_data='admin_users')])
    if role == UserRole.SUPER_ADMIN or perms.get('can_broadcast', True):
        keyboard.append([InlineKeyboardButton("📢 BROADCAST", callback_data='admin_broadcast')])
    if role == UserRole.SUPER_ADMIN or perms.get('can_manage_posts', True):
        keyboard.append([InlineKeyboardButton("📅 AUTO POST (SQLite)", callback_data='admin_posts')])
    if role == UserRole.SUPER_ADMIN or perms.get('can_view_stats', True):
        keyboard.append([InlineKeyboardButton("📊 STATISTIK", callback_data='admin_stats')])
        keyboard.append([InlineKeyboardButton("📋 LOG AKTIVITAS", callback_data='admin_logs')])
    
    if role == UserRole.SUPER_ADMIN:
        keyboard.extend([
            [InlineKeyboardButton("👑 KELOLA ADMIN", callback_data='admin_manage_admins')],
            [InlineKeyboardButton("⚙️ PENGATURAN", callback_data='admin_settings')],
            [InlineKeyboardButton("💾 BACKUP", callback_data='admin_backup')],
        ])
    
    # Tambahkan link ke panel auto post dari script pertama
    if user.id in post_manager.authorized_users:
        keyboard.append([InlineKeyboardButton("📅 AUTO POST (JSON)", callback_data='admin_back')])
    
    keyboard.append([InlineKeyboardButton("🔙 KEMBALI KE MENU", callback_data='back_to_menu')])
    
    await update.message.reply_text(
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    db.log_interaction(user.id, '/admin')
    db.log_admin_action(user.id, 'view_dashboard', 'system', 'admin', 'Viewed admin dashboard')

# ==================== USER MANAGEMENT (dari script kedua) ====================

@role_required(UserRole.ADMIN)
async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /users command"""
    user = update.effective_user
    perms = db.get_admin_permissions(user.id) if db.get_user_role(user.id) == UserRole.ADMIN else {'can_manage_users': True}
    
    if not perms.get('can_manage_users') and db.get_user_role(user.id) != UserRole.SUPER_ADMIN:
        await update.message.reply_text("❌ Anda tidak memiliki izin untuk mengelola user.")
        return
    
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
    
    for u in users[:10]:
        status = "⛔" if u.get('is_blocked') else "✅"
        banned = "🚫" if u.get('is_banned') else ""
        role = "👑" if db.is_admin(u['user_id']) else "👤"
        
        text += f"{status}{banned}{role} `{u['user_id']}` - {u['first_name']}"
        if u.get('username'):
            text += f" @{u['username']}"
        text += f"\n   📅 {u['joined_date'][:10]} | 🕐 {u['last_active'][:16]}\n"
    
    keyboard = []
    if not search_query and total_pages > 1:
        nav_row = []
        if page > 1:
            nav_row.append(InlineKeyboardButton("◀️", callback_data=f'users_page_{page-1}'))
        nav_row.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data='noop'))
        if page < total_pages:
            nav_row.append(InlineKeyboardButton("▶️", callback_data=f'users_page_{page+1}'))
        keyboard.append(nav_row)
    
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

# ==================== SUPER ADMIN COMMANDS (dari script kedua) ====================

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
        'limits': []
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
    
    if value.lower() in ['true', 'false']:
        value_type = 'boolean'
    elif value.isdigit():
        value_type = 'integer'
    else:
        value_type = 'string'
    
    if db.update_setting(key, value, update.effective_user.id, value_type):
        await update.message.reply_text(
            f"✅ Setting `{key}` diubah menjadi `{value}`",
            parse_mode=ParseMode.MARKDOWN
        )
        logger.info(f"⚙️ Setting {key} changed to {value} by {update.effective_user.id}")
    else:
        await update.message.reply_text(f"❌ Gagal mengubah setting `{key}`", parse_mode=ParseMode.MARKDOWN)

@role_required(UserRole.SUPER_ADMIN)
async def block_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /block command"""
    if not context.args:
        await update.message.reply_text("❌ Gunakan: /block [user_id]")
        return
    
    try:
        target_id = int(context.args[0])
        
        if target_id in SUPER_ADMINS:
            await update.message.reply_text("❌ Tidak bisa memblokir super admin!")
            return
        
        if db.block_user(target_id, "Blocked by admin"):
            await update.message.reply_text(f"✅ User `{target_id}` telah diblokir.", parse_mode=ParseMode.MARKDOWN)
            db.log_admin_action(update.effective_user.id, 'block_user', 'user', str(target_id), "Blocked user")
        else:
            await update.message.reply_text(f"❌ User `{target_id}` tidak ditemukan.", parse_mode=ParseMode.MARKDOWN)
    except ValueError:
        await update.message.reply_text("❌ ID user harus berupa angka!")

@role_required(UserRole.SUPER_ADMIN)
async def unblock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /unblock command"""
    if not context.args:
        await update.message.reply_text("❌ Gunakan: /unblock [user_id]")
        return
    
    try:
        target_id = int(context.args[0])
        
        if db.unblock_user(target_id):
            await update.message.reply_text(f"✅ User `{target_id}` telah dibuka blokirnya.", parse_mode=ParseMode.MARKDOWN)
            db.log_admin_action(update.effective_user.id, 'unblock_user', 'user', str(target_id), "Unblocked user")
        else:
            await update.message.reply_text(f"❌ User `{target_id}` tidak ditemukan.", parse_mode=ParseMode.MARKDOWN)
    except ValueError:
        await update.message.reply_text("❌ ID user harus berupa angka!")

@role_required(UserRole.SUPER_ADMIN)
async def backup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /backup command"""
    user = update.effective_user
    
    msg = await update.message.reply_text("💾 Membuat backup database...")
    
    backup_file = db.backup_database()
    
    if backup_file:
        size = os.path.getsize(backup_file)
        size_str = f"{size / 1024:.2f} KB" if size < 1024*1024 else f"{size / (1024*1024):.2f} MB"
        
        await msg.edit_text(
            f"✅ *Backup Berhasil*\n\n"
            f"📁 File: `{backup_file}`\n"
            f"📦 Size: {size_str}\n"
            f"🕐 Waktu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            parse_mode=ParseMode.MARKDOWN
        )
        
        await context.bot.send_document(
            chat_id=user.id,
            document=open(backup_file, 'rb'),
            filename=os.path.basename(backup_file),
            caption="💾 Backup Database"
        )
    else:
        await msg.edit_text("❌ Gagal membuat backup.")
    
    db.log_interaction(user.id, '/backup')

# ==================== BROADCAST COMMANDS (dari script kedua) ====================

@role_required(UserRole.ADMIN)
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /broadcast command"""
    user = update.effective_user
    perms = db.get_admin_permissions(user.id) if db.get_user_role(user.id) == UserRole.ADMIN else {'can_broadcast': True}
    
    if not perms.get('can_broadcast') and db.get_user_role(user.id) != UserRole.SUPER_ADMIN:
        await update.message.reply_text("❌ Anda tidak memiliki izin untuk broadcast.")
        return
    
    text = (
        "📢 *SISTEM BROADCAST*\n\n"
        "Pilih jenis broadcast:\n\n"
        "1️⃣ *Broadcast Teks* - Kirim pesan teks ke semua user\n"
        "2️⃣ *Broadcast dengan Gambar* - Kirim pesan + gambar\n"
        "3️⃣ *Lihat Riwayat* - Lihat broadcast sebelumnya\n\n"
        "Klik tombol di bawah untuk memulai:"
    )
    
    keyboard = [
        [InlineKeyboardButton("📝 BROADCAST TEKS", callback_data='broadcast_text')],
        [InlineKeyboardButton("🖼️ BROADCAST + GAMBAR", callback_data='broadcast_image')],
        [InlineKeyboardButton("📋 LIHAT RIWAYAT", callback_data='broadcast_history')],
        [InlineKeyboardButton("🔙 KEMBALI", callback_data='admin_dashboard')]
    ]
    
    await update.message.reply_text(
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    db.log_interaction(user.id, '/broadcast')

# ==================== AUTO POST COMMANDS (dari script kedua) ====================

@role_required(UserRole.ADMIN)
async def posts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /posts command - untuk SQLite"""
    user = update.effective_user
    perms = db.get_admin_permissions(user.id) if db.get_user_role(user.id) == UserRole.ADMIN else {'can_manage_posts': True}
    
    if not perms.get('can_manage_posts') and db.get_user_role(user.id) != UserRole.SUPER_ADMIN:
        await update.message.reply_text("❌ Anda tidak memiliki izin untuk mengelola auto post.")
        return
    
    posts = db.get_all_posts(include_inactive=True)
    
    text = "📅 *MANAJEMEN AUTO POST (SQLite)*\n\n"
    
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
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM user_interactions WHERE date(timestamp) = date("now")')
        interactions_today = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM user_interactions')
        total_interactions = cursor.fetchone()[0]
    
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
        "📅 *AUTO POST (SQLite)*\n"
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
        f"• Total Interaksi: {total_interactions}\n\n"
        f"⚙️ *VERSI BOT*\n• Ultimate Pro v3.0"
    )
    
    # Tambah info jadwal dari script pertama
    text += f"\n\n📅 *AUTO POST (JSON)*\n"
    text += f"• Total Jadwal: {len(post_manager.posts)}\n"
    text += f"• Jadwal Aktif: {sum(1 for p in post_manager.posts.values() if p.get('active', True))}\n"
    
    keyboard = [[InlineKeyboardButton("🔙 KEMBALI", callback_data='admin_dashboard')]]
    
    await update.message.reply_text(
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    db.log_interaction(user.id, '/stats')

# ==================== BUTTON CALLBACK HANDLER (gabungan) ====================

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all button callbacks"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    data = query.data
    
    logger.info(f"🔘 Button {data} diklik oleh {user.first_name} (ID: {user.id})")
    
    try:
        # ========== USER BUTTONS dari script pertama ==========
        if data == "login":
            text = "🔐 *Link Login*\n\nKlik tombol di bawah untuk login:"
            keyboard = [[InlineKeyboardButton("🔐 LOGIN SEKARANG", url="https://bopel2.link/login")]]
            await query.message.reply_text(
                text=text, 
                parse_mode=ParseMode.MARKDOWN, 
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            await query.delete_message()
        
        elif data == "daftar":
            text = "📝 *Link Daftar*\n\nKlik tombol di bawah untuk mendaftar:"
            keyboard = [[InlineKeyboardButton("📝 DAFTAR SEKARANG", url="https://bopel2.link/daftar")]]
            await query.message.reply_text(
                text=text, 
                parse_mode=ParseMode.MARKDOWN, 
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            await query.delete_message()
        
        elif data == "claim":
            text = "🎁 *Claim Event Parlay*\n\nKlik tombol di bawah untuk klaim bonus:"
            keyboard = [[InlineKeyboardButton("🎁 CLAIM BONUS", url="https://bopel2.link/wa")]]
            await query.message.reply_text(
                text=text, 
                parse_mode=ParseMode.MARKDOWN, 
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            await query.delete_message()
        
        elif data == "promo":
            await send_promo(query.message, context)
            await query.delete_message()
        
        elif data == "menu_utama" or data == "back_to_menu":
            await start_command(update, context)
        
        # ========== ADMIN BUTTONS dari script pertama ==========
        elif data.startswith('admin_'):
            if user.id not in post_manager.authorized_users:
                await query.message.reply_text("❌ Anda tidak diizinkan.")
                return
            
            if data == 'admin_list':
                if not post_manager.posts:
                    text = "📋 Belum ada jadwal tersedia."
                else:
                    text = "📋 *DAFTAR JADWAL AUTO POST*\n\n"
                    for post_id, post in post_manager.posts.items():
                        status = "✅" if post.get('active', True) else "❌"
                        has_image = "📷" if post.get('image_url') else "📝"
                        text += f"{has_image} ID {post_id}: {post.get('time')} {status}\n"
                
                await query.message.edit_text(
                    text=text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 KEMBALI", callback_data='admin_back')
                    ]])
                )
            
            elif data == 'admin_add':
                post_manager.pending_input[user.id] = {
                    'action': 'add',
                    'step': 'time'
                }
                await query.message.edit_text(
                    "🕐 *TAMBAH JADWAL BARU - LANGKAH 1/4*\n\n"
                    "Masukkan waktu pengiriman dalam format *HH:MM*\n"
                    "Contoh: `14:30`\n\n"
                    "Ketik *batal* untuk membatalkan.",
                    parse_mode=ParseMode.MARKDOWN
                )
            
            elif data == 'admin_next':
                next_run = post_manager.get_next_run_time()
                if next_run:
                    text = f"⏰ *JADWAL BERIKUTNYA*\n\n{next_run.strftime('%d %B %Y, %H:%M:%S')}"
                else:
                    text = "⚠️ Tidak ada jadwal aktif"
                
                await query.message.edit_text(
                    text=text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 KEMBALI", callback_data='admin_back')
                    ]])
                )
            
            elif data == 'admin_back':
                text = (
                    "🔧 *PANEL ADMIN AUTO POST*\n\n"
                    "Pilih menu:"
                )
                keyboard = [
                    [InlineKeyboardButton("📋 LIST JADWAL", callback_data='admin_list')],
                    [InlineKeyboardButton("➕ TAMBAH JADWAL", callback_data='admin_add')],
                    [InlineKeyboardButton("🔄 CEK JADWAL BERIKUTNYA", callback_data='admin_next')],
                    [InlineKeyboardButton("🔙 KEMBALI KE MENU", callback_data='menu_utama')]
                ]
                await query.message.edit_text(
                    text=text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
        
        # ========== EDIT FIELD BUTTONS dari script pertama ==========
        elif data.startswith('edit_field_'):
            parts = data.split('_')
            field = parts[2]
            post_id = parts[3]
            
            if field == 'time':
                post_manager.pending_input[user.id] = {
                    'action': 'edit',
                    'post_id': post_id,
                    'step': 'time'
                }
                await query.message.edit_text(
                    f"🕐 *EDIT WAKTU ID {post_id}*\n\n"
                    "Masukkan waktu baru dalam format HH:MM\n"
                    "Contoh: 14:30\n\n"
                    "Ketik *batal* untuk membatalkan.",
                    parse_mode=ParseMode.MARKDOWN
                )
            
            elif field == 'text':
                post_manager.pending_input[user.id] = {
                    'action': 'edit',
                    'post_id': post_id,
                    'step': 'text'
                }
                await query.message.edit_text(
                    f"📝 *EDIT TEKS ID {post_id}*\n\n"
                    "Masukkan teks baru:\n\n"
                    "Ketik *batal* untuk membatalkan.",
                    parse_mode=ParseMode.MARKDOWN
                )
            
            elif field == 'image':
                post_manager.pending_input[user.id] = {
                    'action': 'edit',
                    'post_id': post_id,
                    'step': 'image'
                }
                await query.message.edit_text(
                    f"📷 *EDIT GAMBAR ID {post_id}*\n\n"
                    "Masukkan URL gambar baru\n"
                    "Ketik *-* untuk menghapus gambar\n\n"
                    "Ketik *batal* untuk membatalkan.",
                    parse_mode=ParseMode.MARKDOWN
                )
            
            elif field == 'active':
                post = post_manager.posts.get(post_id, {})
                current = post.get('active', True)
                new_status = not current
                post_manager.update_post(post_id, active=new_status)
                
                status_text = "diaktifkan" if new_status else "dinonaktifkan"
                await query.message.edit_text(
                    f"✅ Jadwal ID {post_id} telah {status_text}.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 KEMBALI", callback_data='admin_list')
                    ]])
                )
                
                await scheduler.schedule_next_run(context)
        
        # ========== ADMIN DASHBOARD dari script kedua ==========
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
                f"• Total Jadwal SQLite: {len(posts)}\n"
                f"• Jadwal Aktif SQLite: {active_posts}\n"
                f"• Total Jadwal JSON: {len(post_manager.posts)}\n"
            )
            
            keyboard = []
            perms = db.get_admin_permissions(user.id) if role == UserRole.ADMIN else {}
            
            if role == UserRole.SUPER_ADMIN or perms.get('can_manage_users', True):
                keyboard.append([InlineKeyboardButton("👥 MANAJEMEN USER", callback_data='admin_users')])
            if role == UserRole.SUPER_ADMIN or perms.get('can_broadcast', True):
                keyboard.append([InlineKeyboardButton("📢 BROADCAST", callback_data='admin_broadcast')])
            if role == UserRole.SUPER_ADMIN or perms.get('can_manage_posts', True):
                keyboard.append([InlineKeyboardButton("📅 AUTO POST (SQLite)", callback_data='admin_posts')])
            if role == UserRole.SUPER_ADMIN or perms.get('can_view_stats', True):
                keyboard.append([InlineKeyboardButton("📊 STATISTIK", callback_data='admin_stats')])
                keyboard.append([InlineKeyboardButton("📋 LOG AKTIVITAS", callback_data='admin_logs')])
            
            if role == UserRole.SUPER_ADMIN:
                keyboard.extend([
                    [InlineKeyboardButton("👑 KELOLA ADMIN", callback_data='admin_manage_admins')],
                    [InlineKeyboardButton("⚙️ PENGATURAN", callback_data='admin_settings')],
                    [InlineKeyboardButton("💾 BACKUP", callback_data='admin_backup')],
                ])
            
            if user.id in post_manager.authorized_users:
                keyboard.append([InlineKeyboardButton("📅 AUTO POST (JSON)", callback_data='admin_back')])
            
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
                [InlineKeyboardButton("📊 STATISTIK USER", callback_data='user_stats')],
            ]
            
            if db.is_super_admin(user.id):
                keyboard.append([InlineKeyboardButton("⛔ BLOKIR USER", callback_data='user_block')])
            
            keyboard.append([InlineKeyboardButton("🔙 KEMBALI", callback_data='admin_dashboard')])
            
            await query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        elif data == "admin_broadcast":
            if not db.is_admin(user.id):
                return
            
            if db.get_user_role(user.id) == UserRole.ADMIN:
                perms = db.get_admin_permissions(user.id)
                if not perms.get('can_broadcast', True):
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
                [InlineKeyboardButton("📋 LIHAT RIWAYAT", callback_data='broadcast_history')],
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
            
            if db.get_user_role(user.id) == UserRole.ADMIN:
                perms = db.get_admin_permissions(user.id)
                if not perms.get('can_manage_posts', True):
                    await query.message.reply_text("❌ Anda tidak memiliki izin untuk mengelola auto post.")
                    return
            
            posts = db.get_all_posts(include_inactive=True)
            
            text = "📅 *MANAJEMEN AUTO POST (SQLite)*\n\n"
            
            if posts:
                for post in posts[:5]:
                    status = "✅" if post['is_active'] else "❌"
                    text += f"{status} ID {post['post_id']}: {post['time']}\n"
                    preview = post['text'][:30] + '...' if len(post['text']) > 30 else post['text']
                    text += f"   `{preview}`\n"
                if len(posts) > 5:
                    text += f"\n...dan {len(posts)-5} jadwal lainnya\n"
            else:
                text += "Belum ada jadwal.\n\n"
            
            text += "\nPilih menu:"
            
            keyboard = [
                [InlineKeyboardButton("➕ TAMBAH", callback_data='posts_add'),
                 InlineKeyboardButton("✏️ EDIT", callback_data='posts_edit')],
                [InlineKeyboardButton("❌ HAPUS", callback_data='posts_delete'),
                 InlineKeyboardButton("🔄 AKTIF/NONAKTIF", callback_data='posts_toggle')],
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
            
            if db.get_user_role(user.id) == UserRole.ADMIN:
                perms = db.get_admin_permissions(user.id)
                if not perms.get('can_view_stats', True):
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
                "📅 *AUTO POST (SQLite)*\n"
                f"• Total Jadwal: {len(posts)}\n"
                f"• Aktif: {sum(1 for p in posts if p['is_active'])}\n\n"
                "📢 *BROADCAST*\n"
                f"• Total: {broadcast_stats['total']}\n"
                f"• Terkirim: {broadcast_stats['sent']}\n"
                f"• Success Rate: {broadcast_stats['success_rate']:.1f}%\n\n"
                "📋 *AKTIVITAS*\n"
                f"• Interaksi Hari Ini: {interactions_today}\n"
                f"• Log Admin Hari Ini: {logs_today}\n"
                f"• Jadwal JSON: {len(post_manager.posts)}\n"
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
                "💾 *BACKUP DATABASE*\n\n"
                "Pilih opsi:"
            )
            
            keyboard = [
                [InlineKeyboardButton("📤 BUAT BACKUP", callback_data='backup_create')],
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
            
            # Ini untuk SQLite
            context.user_data['post_step_sql'] = 'time'
            await query.message.edit_text(
                "➕ *TAMBAH JADWAL (SQLite)*\n\n"
                "Langkah 1/4: Masukkan waktu (HH:MM)\n"
                "Contoh: `14:30`\n\n"
                "Ketik *batal* untuk membatalkan.",
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif data == "posts_list":
            if not db.is_admin(user.id):
                return
            
            posts = db.get_all_posts(include_inactive=True)
            
            if not posts:
                text = "📋 *SEMUA JADWAL (SQLite)*\n\nBelum ada jadwal."
            else:
                text = "📋 *SEMUA JADWAL AUTO POST (SQLite)*\n\n"
                for post in posts:
                    status = "✅" if post['is_active'] else "❌"
                    text += f"{status} *ID {post['post_id']}* | {post['time']}\n"
                    text += f"   `{post['text'][:100]}`\n"
                    if post.get('image_url'):
                        text += f"   📷 Gambar: {post['image_url'][:50]}...\n"
                    text += "\n"
            
            keyboard = [[InlineKeyboardButton("🔙 KEMBALI", callback_data='admin_posts')]]
            
            await query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        # ========== USER STATS ==========
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
        
        elif data == "noop":
            pass
        
    except Exception as e:
        logger.error(f"❌ Error in button_callback: {e}")
        await query.message.reply_text(
            "❌ Terjadi kesalahan. Silakan coba lagi nanti."
        )

# ==================== FUNGSI KIRIM PROMO ====================

async def send_promo(message, context):
    """Kirim promo dengan gambar (dari script pertama)"""
    try:
        keyboard = [
            [InlineKeyboardButton("🤖 BOT OFFICIAL", url="https://t.me/bolapelangi2_bot")],
            [InlineKeyboardButton("📈 PREDIKSI JITU", url="https://bopel2.vip/ChannelWA-Jadwal-Prediksi")],
            [InlineKeyboardButton("📢 CHANNEL WA", url="https://bopel2.vip/Channel-Whatsapp")],
            [InlineKeyboardButton("📢 CHANNEL TG", url="https://bopel2.vip/Channel-Telegram")],
            [InlineKeyboardButton("🟢 KLAIM BONUS", url="https://bopel2.link/wa")],
            [InlineKeyboardButton("🔙 KEMBALI KE MENU", callback_data="menu_utama")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        image_url = None
        for post in post_manager.posts.values():
            if post.get('image_url'):
                image_url = post['image_url']
                break
        
        if not image_url:
            image_url = config.get('images.default_promo', "https://i.ibb.co/your-image/promo-banner.jpg")
        
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
        logger.error(f"❌ Gagal kirim promo: {e}")

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
                buttons=json.loads(broadcast['buttons']) if broadcast['buttons'] else None
            )
        )

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
        
        os.makedirs('data', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        os.makedirs('backups', exist_ok=True)
        logger.info("✅ Created required folders")
        
        commands = [
            BotCommand("start", "Mulai bot"),
            BotCommand("help", "Bantuan"),
            BotCommand("info", "Info akun"),
            BotCommand("promo", "Lihat promo"),
            BotCommand("stats", "Statistik bot"),
            BotCommand("admin", "Panel admin"),
            BotCommand("list_jadwal", "Lihat jadwal auto post"),
            BotCommand("tambah_jadwal", "Tambah jadwal auto post"),
        ]
        
        await application.bot.set_my_commands(commands)
        logger.info("✅ Bot commands set")
        
        job_queue = application.job_queue
        if job_queue:
            job_queue.run_repeating(check_auto_posts_job, interval=60, first=10)
            job_queue.run_repeating(check_scheduled_broadcasts_job, interval=300, first=30)
            logger.info("✅ Jobs scheduled")
        
        try:
            await application.bot.send_message(
                chat_id=CHANNEL_ID,
                text="🤖 *Bot Ultimate Pro v3.0 Aktif*\n\n✅ Sistem auto post & broadcast siap!",
                parse_mode=ParseMode.MARKDOWN
            )
            logger.info("✅ Startup message sent to channel")
        except Exception as e:
            logger.error(f"❌ Cannot send to channel: {e}")
        
        user_stats = db.get_user_count()
        logger.info(f"✅ Total users: {user_stats['total']}")
        logger.info(f"✅ Total admins: {len(db.get_all_admins())}")
        logger.info(f"✅ Total auto posts (JSON): {len(post_manager.posts)}")
        
        # Jadwalkan pengecekan pertama
        await scheduler.schedule_next_run(application)
        
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
    print("   ✅ Auto Post Terjadwal (JSON & SQLite)")
    print("   ✅ Broadcast System with Queue")
    print("   ✅ Database SQLite dengan Backup")
    print("   ✅ Admin Management")
    print("   ✅ User Tracking & Analytics")
    print("   ✅ Super Admin Protection")
    print("   ✅ Statistics & Logs")
    print("   ✅ Config via Telegram")
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
    
    # Command handlers dari script pertama
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("list_jadwal", list_jadwal_command))
    application.add_handler(CommandHandler("tambah_jadwal", tambah_jadwal_command))
    application.add_handler(CommandHandler("edit_jadwal", edit_jadwal_command))
    application.add_handler(CommandHandler("hapus_jadwal", hapus_jadwal_command))
    application.add_handler(CommandHandler("aktifkan_jadwal", aktifkan_jadwal_command))
    application.add_handler(CommandHandler("nonaktifkan_jadwal", nonaktifkan_jadwal_command))
    
    # Command handlers dari script kedua
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("info", info_command))
    application.add_handler(CommandHandler("promo", promo_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("test_channel", test_channel_command))
    
    # Admin commands dari script kedua
    application.add_handler(CommandHandler("admin_panel", admin_panel_command))  # admin panel utama
    application.add_handler(CommandHandler("users", users_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("posts", posts_command))
    
    # Super admin commands
    application.add_handler(CommandHandler("admins", admins_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CommandHandler("set", set_command))
    application.add_handler(CommandHandler("block", block_command))
    application.add_handler(CommandHandler("unblock", unblock_command))
    application.add_handler(CommandHandler("backup", backup_command))
    
    # Message handler untuk input
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input))
    
    # Callback handler
    application.add_handler(CallbackQueryHandler(button_callback))
    
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
    print("📢 Fitur: Auto Welcome | Auto Post (JSON+SQLite) | Broadcast | Admin Panel")
    print("📢 Database: SQLite dengan auto backup")
    print("📢 Super Admin: @Bolapelangi2 & @bolapelangi_2")
    print("=" * 80)
    sys.stdout.flush()
    
    application.run_polling(
        allowed_updates=["message", "channel_post", "callback_query"],
        drop_pending_updates=True
    )

if __name__ == "__main__":
    main()
