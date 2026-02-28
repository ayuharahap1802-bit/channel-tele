"""
TELEGRAM BOT SUPER LENGKAP - BOLAPELANGI 2
VERSI: ULTIMATE DENGAN DATABASE & BROADCAST
Fitur: Auto Welcome | Auto Post Scheduler | Broadcast | Admin Panel | User Tracking
Created for: @bolapelangi2_bot
Author: Sistem Profesional
"""

import os
import logging
import sys
import asyncio
import json
import sqlite3
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from contextlib import contextmanager
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode

# ==================== LOAD ENVIRONMENT VARIABLES ====================

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv tidak wajib

print("=" * 70)
print("🔍 MEMULAI BOT BOLAPELANGI 2 ULTIMATE EDITION...")
print("=" * 70)

# ==================== LOAD CONFIGURATION FROM JSON ====================

def load_config():
    """Load configuration from JSON files"""
    config = {
        'bot': {},
        'super_admins': [],
        'database': {},
        'features': {},
        'broadcast': {},
        'urls': {},
        'images': {},
        'limits': {}
    }
    
    # Load main config dari folder data
    config_path = os.path.join('data', 'config.json')
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                loaded_config = json.load(f)
                config.update(loaded_config)
            print(f"✅ Loaded config from {config_path}")
        except Exception as e:
            print(f"⚠️ Gagal load config: {e}")
    else:
        print("⚠️ File config.json tidak ditemukan, menggunakan default")
    
    return config

# Load config
config = load_config()

# ==================== KONFIGURASI DARI ENVIRONMENT ====================

# Baca dari environment variable (prioritas utama)
BOT_TOKEN = os.environ.get("BOT_TOKEN") or config.get('bot', {}).get('token')
CHANNEL_ID_STR = os.environ.get("CHANNEL_ID") or str(config.get('bot', {}).get('channel_id', '-1003573191693'))
DATABASE_FILE = os.environ.get("DATABASE_FILE") or config.get('database', {}).get('file', 'bot_database.db')

print(f"🔍 BOT_TOKEN: {'ADA' if BOT_TOKEN else 'TIDAK ADA'}")
print(f"🔍 CHANNEL_ID: {CHANNEL_ID_STR}")
print(f"🔍 DATABASE: {DATABASE_FILE}")

# Fallback ke default
if not BOT_TOKEN:
    BOT_TOKEN = "8793227199:AAEXajy3RDO7SpMSCloj13Z4ubX3DXNvN4M"
    print("⚠️ Pakai BOT_TOKEN default")

if not CHANNEL_ID_STR:
    CHANNEL_ID_STR = "-1003573191693"
    print("⚠️ Pakai CHANNEL_ID default")

# Konversi CHANNEL_ID
try:
    CHANNEL_ID = int(CHANNEL_ID_STR)
    print(f"✅ CHANNEL_ID: {CHANNEL_ID}")
except:
    CHANNEL_ID = -1003573191693
    print(f"⚠️ CHANNEL_ID forced: {CHANNEL_ID}")

print(f"✅ BOT_TOKEN: {BOT_TOKEN[:10]}...{BOT_TOKEN[-5:]}")

# ==================== SUPER ADMIN ====================

SUPER_ADMINS = config.get('super_admins', [
    850434834,      # @Bolapelangi2
    8122523608      # @bolapelangi_2
])

print(f"✅ SUPER ADMIN: {SUPER_ADMINS}")

# ==================== URLS ====================

URLS = config.get('urls', {
    "login": "https://bopel2.link/login",
    "daftar": "https://bopel2.link/daftar",
    "claim": "https://bopel2.link/wa",
    "bot_official": "https://t.me/bolapelangi2_bot",
    "prediksi": "https://bopel2.vip/ChannelWA-Jadwal-Prediksi",
    "channel_wa": "https://bopel2.vip/Channel-Whatsapp",
    "channel_tg": "https://bopel2.vip/Channel-Telegram"
})

# ==================== KONFIGURASI LOGGING ====================

# Buat folder logs jika belum ada
os.makedirs('logs', exist_ok=True)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/bot_activity.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# ==================== TEKS PROMO DEFAULT ====================

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
    bot_official=URLS['bot_official'],
    prediksi=URLS['prediksi'],
    channel_wa=URLS['channel_wa'],
    channel_tg=URLS['channel_tg'],
    claim=URLS['claim']
)

# ==================== DATABASE MANAGER ====================

class DatabaseManager:
    """Manager database SQLite untuk menyimpan semua data bot"""
    
    def __init__(self, db_file: str = DATABASE_FILE):
        self.db_file = db_file
        # Buat folder database jika perlu
        db_dir = os.path.dirname(db_file)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        self.init_database()
        logger.info("✅ Database Manager initialized")
    
    @contextmanager
    def get_connection(self):
        """Context manager untuk koneksi database"""
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
    
    def init_database(self):
        """Inisialisasi semua tabel database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabel users
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
                    notes TEXT
                )
            ''')
            
            # Tabel admins
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admins (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    added_by INTEGER,
                    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    permissions TEXT DEFAULT 'all',
                    is_super BOOLEAN DEFAULT 0,
                    FOREIGN KEY (added_by) REFERENCES users(user_id)
                )
            ''')
            
            # Tabel auto_posts
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
                    FOREIGN KEY (created_by) REFERENCES users(user_id)
                )
            ''')
            
            # Tabel broadcast_messages
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
                    total_recipients INTEGER,
                    success_count INTEGER DEFAULT 0,
                    failed_count INTEGER DEFAULT 0,
                    FOREIGN KEY (created_by) REFERENCES users(user_id)
                )
            ''')
            
            # Tabel broadcast_recipients
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS broadcast_recipients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    broadcast_id INTEGER,
                    user_id INTEGER,
                    sent_status TEXT DEFAULT 'pending',
                    sent_time TIMESTAMP,
                    error_message TEXT,
                    FOREIGN KEY (broadcast_id) REFERENCES broadcast_messages(broadcast_id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # Tabel user_interactions
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    command TEXT,
                    message_text TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # Tabel settings
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_by INTEGER,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insert super admins jika belum ada
            for admin_id in SUPER_ADMINS:
                cursor.execute('''
                    INSERT OR IGNORE INTO admins (user_id, is_super, permissions)
                    VALUES (?, 1, 'super_admin')
                ''', (admin_id,))
            
            # Insert default settings
            default_settings = [
                ('welcome_enabled', str(config.get('features', {}).get('welcome_enabled', True)).lower()),
                ('auto_post_enabled', str(config.get('features', {}).get('auto_post_enabled', True)).lower()),
                ('broadcast_delay', str(config.get('broadcast', {}).get('delay_between_messages', 1))),
                ('max_broadcast_per_day', str(config.get('broadcast', {}).get('max_per_day', 5))),
                ('bot_name', config.get('bot', {}).get('name', 'BOLAPELANGI 2 Bot')),
                ('support_contact', '@admin'),
            ]
            for key, value in default_settings:
                cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', (key, value))
    
    # ========== USER MANAGEMENT ==========
    
    def add_or_update_user(self, user: Any) -> bool:
        """Tambah atau update user di database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO users (
                        user_id, username, first_name, last_name, 
                        language_code, is_bot, last_active, total_interactions
                    ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 1)
                    ON CONFLICT(user_id) DO UPDATE SET
                        username = excluded.username,
                        first_name = excluded.first_name,
                        last_name = excluded.last_name,
                        language_code = excluded.language_code,
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
            logger.error(f"❌ Gagal update user {user.id}: {e}")
            return False
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Ambil data user berdasarkan ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_users(self, include_blocked: bool = False) -> List[Dict]:
        """Ambil semua user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if include_blocked:
                cursor.execute('SELECT * FROM users ORDER BY joined_date DESC')
            else:
                cursor.execute('SELECT * FROM users WHERE is_blocked = 0 ORDER BY joined_date DESC')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_user_count(self) -> Dict:
        """Dapatkan statistik user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) as total FROM users')
            total = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) as today FROM users WHERE date(joined_date) = date("now")')
            today = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) as active FROM users WHERE last_active > datetime("now", "-1 day")')
            active = cursor.fetchone()[0]
            
            return {
                'total': total,
                'today': today,
                'active': active
            }
    
    # ========== ADMIN MANAGEMENT ==========
    
    def is_admin(self, user_id: int) -> bool:
        """Cek apakah user adalah admin"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM admins WHERE user_id = ?', (user_id,))
            return cursor.fetchone() is not None
    
    def is_super_admin(self, user_id: int) -> bool:
        """Cek apakah user adalah super admin"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT is_super FROM admins WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            return row and row['is_super'] == 1
    
    def add_admin(self, user_id: int, added_by: int, username: str = None, permissions: str = 'all') -> bool:
        """Tambah admin baru (hanya oleh super admin)"""
        try:
            if not self.is_super_admin(added_by):
                return False
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO admins (user_id, username, added_by, permissions, is_super)
                    VALUES (?, ?, ?, ?, 0)
                ''', (user_id, username, added_by, permissions))
                return True
        except Exception as e:
            logger.error(f"❌ Gagal tambah admin {user_id}: {e}")
            return False
    
    def remove_admin(self, user_id: int, removed_by: int) -> bool:
        """Hapus admin (hanya oleh super admin)"""
        try:
            if not self.is_super_admin(removed_by):
                return False
            
            if user_id in SUPER_ADMINS:
                return False
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM admins WHERE user_id = ?', (user_id,))
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"❌ Gagal hapus admin {user_id}: {e}")
            return False
    
    def get_all_admins(self) -> List[Dict]:
        """Ambil semua admin"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT a.*, u.first_name, u.username 
                FROM admins a
                LEFT JOIN users u ON a.user_id = u.user_id
                ORDER BY a.is_super DESC, a.added_date
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    # ========== BROADCAST MANAGEMENT ==========
    
    def create_broadcast(self, created_by: int, message_text: str, message_type: str = 'text', 
                         file_id: str = None, caption: str = None, buttons: Dict = None) -> int:
        """Buat broadcast baru"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO broadcast_messages (
                        message_text, message_type, file_id, caption, buttons, created_by, status
                    ) VALUES (?, ?, ?, ?, ?, ?, 'draft')
                ''', (message_text, message_type, file_id, caption, json.dumps(buttons) if buttons else None, created_by))
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"❌ Gagal create broadcast: {e}")
            return -1
    
    def schedule_broadcast(self, broadcast_id: int, schedule_time: datetime) -> bool:
        """Jadwalkan broadcast"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE broadcast_messages 
                    SET scheduled_time = ?, status = 'scheduled'
                    WHERE broadcast_id = ?
                ''', (schedule_time.isoformat(), broadcast_id))
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"❌ Gagal schedule broadcast: {e}")
            return False
    
    def get_pending_broadcasts(self) -> List[Dict]:
        """Ambil broadcast yang pending"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM broadcast_messages 
                WHERE status = 'scheduled' 
                AND scheduled_time <= datetime('now')
                ORDER BY scheduled_time
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_broadcasts(self, limit: int = 50) -> List[Dict]:
        """Ambil semua broadcast"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT b.*, u.username as creator_username, u.first_name as creator_name
                FROM broadcast_messages b
                LEFT JOIN users u ON b.created_by = u.user_id
                ORDER BY b.created_at DESC
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def update_broadcast_status(self, broadcast_id: int, status: str, success: int = 0, failed: int = 0):
        """Update status broadcast"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE broadcast_messages 
                SET status = ?, success_count = success_count + ?, 
                    failed_count = failed_count + ?, sent_time = CURRENT_TIMESTAMP
                WHERE broadcast_id = ?
            ''', (status, success, failed, broadcast_id))
    
    # ========== AUTO POST MANAGEMENT ==========
    
    def get_all_posts(self) -> List[Dict]:
        """Ambil semua jadwal auto post"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM auto_posts ORDER BY time')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_post(self, post_id: int) -> Optional[Dict]:
        """Ambil satu post berdasarkan ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM auto_posts WHERE post_id = ?', (post_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def add_post(self, time_str: str, text: str, image_url: str = None, 
                 button_text: str = None, button_url: str = None, created_by: int = None) -> int:
        """Tambah jadwal post baru"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO auto_posts (time, text, image_url, button_text, button_url, created_by)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (time_str, text, image_url, button_text, button_url, created_by))
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"❌ Gagal tambah post: {e}")
            return -1
    
    def update_post(self, post_id: int, **kwargs) -> bool:
        """Update jadwal post"""
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
            logger.error(f"❌ Gagal update post {post_id}: {e}")
            return False
    
    def delete_post(self, post_id: int) -> bool:
        """Hapus jadwal post"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM auto_posts WHERE post_id = ?', (post_id,))
            return cursor.rowcount > 0
    
    def toggle_post(self, post_id: int) -> bool:
        """Toggle active status post"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE auto_posts SET is_active = NOT is_active WHERE post_id = ?', (post_id,))
            return cursor.rowcount > 0
    
    # ========== INTERACTION LOGGING ==========
    
    def log_interaction(self, user_id: int, command: str, message_text: str = None):
        """Log interaksi user"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO user_interactions (user_id, command, message_text)
                    VALUES (?, ?, ?)
                ''', (user_id, command, message_text))
        except Exception as e:
            logger.error(f"❌ Gagal log interaksi: {e}")
    
    # ========== SETTINGS ==========
    
    def get_setting(self, key: str, default: str = None) -> str:
        """Ambil setting"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
            row = cursor.fetchone()
            return row['value'] if row else default
    
    def update_setting(self, key: str, value: str, updated_by: int) -> bool:
        """Update setting"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE settings SET value = ?, updated_by = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE key = ?
                ''', (value, updated_by, key))
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"❌ Gagal update setting {key}: {e}")
            return False

# ==================== INISIALISASI DATABASE ====================

db = DatabaseManager()

# ==================== AUTO POST SCHEDULER ====================

class AutoPostScheduler:
    """Manager untuk auto posting terjadwal"""
    
    def __init__(self):
        self.running = True
        logger.info("✅ AutoPostScheduler initialized")
    
    async def check_and_send_posts(self, context: ContextTypes.DEFAULT_TYPE):
        """Cek dan kirim postingan yang waktunya sudah tiba"""
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        
        # Ambil semua post aktif
        posts = db.get_all_posts()
        
        for post in posts:
            if not post['is_active']:
                continue
            
            # Cek waktu
            if post['time'] == current_time:
                await self.send_post(context, post)
    
    async def send_post(self, context: ContextTypes.DEFAULT_TYPE, post: Dict):
        """Kirim postingan ke channel"""
        try:
            logger.info(f"📢 Mengirim auto post ID {post['post_id']} - {post['time']}")
            
            # Buat keyboard jika ada button
            reply_markup = None
            if post.get('button_text') and post.get('button_url'):
                keyboard = [[InlineKeyboardButton(post['button_text'], url=post['button_url'])]]
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
                    logger.info(f"✅ Auto post {post['post_id']} terkirim dengan gambar")
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
                logger.info(f"✅ Auto post {post['post_id']} terkirim")
                
        except Exception as e:
            logger.error(f"❌ Gagal auto post {post['post_id']}: {e}")

scheduler = AutoPostScheduler()

# ==================== BROADCAST MANAGER ====================

class BroadcastManager:
    """Manager untuk mengirim broadcast ke semua user"""
    
    def __init__(self):
        self.current_broadcast = None
        self.broadcast_queue = asyncio.Queue()
        logger.info("✅ BroadcastManager initialized")
    
    async def send_broadcast(self, context: ContextTypes.DEFAULT_TYPE, 
                            broadcast_id: int, message_text: str, 
                            message_type: str = 'text', file_id: str = None,
                            caption: str = None, buttons: Dict = None):
        """Kirim broadcast ke semua user"""
        
        # Ambil semua user
        users = db.get_all_users()
        total_users = len(users)
        
        if total_users == 0:
            logger.warning("⚠️ Tidak ada user untuk broadcast")
            return
        
        # Update broadcast dengan total recipient
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE broadcast_messages SET total_recipients = ?, status = "sending" WHERE broadcast_id = ?', 
                          (total_users, broadcast_id))
        
        # Buat keyboard jika ada
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
        
        # Kirim ke setiap user
        success = 0
        failed = 0
        delay = float(db.get_setting('broadcast_delay', '1'))
        
        for user in users:
            user_id = user['user_id']
            
            # Skip blocked users
            if user.get('is_blocked', 0):
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
                
                # Log recipient success
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO broadcast_recipients (broadcast_id, user_id, sent_status, sent_time)
                        VALUES (?, ?, 'success', CURRENT_TIMESTAMP)
                    ''', (broadcast_id, user_id))
                
            except Exception as e:
                failed += 1
                logger.error(f"❌ Gagal broadcast ke {user_id}: {e}")
                
                # Log recipient failed
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO broadcast_recipients (broadcast_id, user_id, sent_status, error_message)
                        VALUES (?, ?, 'failed', ?)
                    ''', (broadcast_id, user_id, str(e)[:200]))
            
            # Delay untuk menghindari flood
            await asyncio.sleep(delay)
        
        # Update final status
        db.update_broadcast_status(broadcast_id, 'sent', success, failed)
        
        logger.info(f"✅ Broadcast {broadcast_id} selesai: {success} success, {failed} failed")
        return {'success': success, 'failed': failed, 'total': total_users}
    
    async def process_broadcast_queue(self, context: ContextTypes.DEFAULT_TYPE):
        """Proses antrian broadcast"""
        while True:
            try:
                broadcast_data = await self.broadcast_queue.get()
                await self.send_broadcast(context, **broadcast_data)
            except Exception as e:
                logger.error(f"❌ Error processing broadcast: {e}")
            await asyncio.sleep(1)

broadcast_manager = BroadcastManager()

# ==================== DECORATORS ====================

def admin_required(func):
    """Decorator untuk memeriksa apakah user adalah admin"""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        if not db.is_admin(user.id):
            await update.message.reply_text(
                "❌ *Akses Ditolak*\n\nAnda tidak memiliki izin untuk menggunakan perintah ini.",
                parse_mode=ParseMode.MARKDOWN
            )
            logger.warning(f"⚠️ Akses ditolak untuk user {user.id} ({user.first_name})")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

def super_admin_required(func):
    """Decorator untuk memeriksa apakah user adalah super admin"""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        if not db.is_super_admin(user.id):
            await update.message.reply_text(
                "❌ *Super Admin Only*\n\nPerintah ini hanya untuk super admin.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

# ==================== COMMAND HANDLERS ====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    
    # Simpan user ke database
    db.add_or_update_user(user)
    db.log_interaction(user.id, '/start')
    
    logger.info(f"🚀 /start dari {user.first_name} (ID: {user.id}, Username: @{user.username})")
    
    # Cek apakah user di-block
    user_data = db.get_user(user.id)
    if user_data and user_data.get('is_blocked'):
        await update.message.reply_text(
            "❌ *Akses Diblokir*\n\nMaaf, akses Anda telah diblokir oleh admin.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    text = (
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
    
    # Button menu
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
    
    # Tambah button admin jika user adalah admin
    if db.is_admin(user.id):
        keyboard.append([InlineKeyboardButton("⚙️ PANEL ADMIN", callback_data='admin_dashboard')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    user = update.effective_user
    db.add_or_update_user(user)
    db.log_interaction(user.id, '/help')
    
    text = (
        "📚 *BANTUAN BOT*\n\n"
        "✨ *Perintah untuk Semua User:*\n"
        "• /start - Mulai bot\n"
        "• /promo - Lihat promo terbaru\n"
        "• /help - Tampilkan bantuan ini\n"
        "• /info - Info akun Anda\n\n"
    )
    
    # Tambah perintah admin jika user adalah admin
    if db.is_admin(user.id):
        text += (
            "\n👑 *Perintah Admin:*\n"
            "• /admin - Dashboard admin\n"
            "• /stats - Statistik bot\n"
            "• /users - Daftar user\n"
            "• /broadcast - Kirim broadcast\n"
            "• /posts - Kelola auto post\n"
        )
    
    # Tambah perintah super admin
    if db.is_super_admin(user.id):
        text += (
            "\n⭐ *Perintah Super Admin:*\n"
            "• /admins - Kelola admin\n"
            "• /settings - Pengaturan bot\n"
            "• /block [user_id] - Blokir user\n"
            "• /unblock [user_id] - Buka blokir\n"
        )
    
    text += f"\n📞 *Kontak Support:*\n{db.get_setting('support_contact', '@admin')}"
    
    keyboard = [[InlineKeyboardButton("🔙 KEMBALI KE MENU", callback_data='back_to_menu')]]
    
    await update.message.reply_text(
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /info command - Lihat info akun"""
    user = update.effective_user
    db.add_or_update_user(user)
    
    user_data = db.get_user(user.id)
    
    text = (
        f"👤 *INFO AKUN ANDA*\n\n"
        f"🆔 *User ID:* `{user.id}`\n"
        f"👤 *Nama:* {user.first_name} {user.last_name or ''}\n"
        f"📛 *Username:* @{user.username or 'tidak ada'}\n"
        f"🌍 *Bahasa:* {user.language_code or 'id'}\n"
        f"📅 *Bergabung:* {user_data['joined_date'] if user_data else 'Sekarang'}\n"
        f"🕐 *Terakhir Aktif:* {user_data['last_active'] if user_data else 'Sekarang'}\n"
        f"📊 *Total Interaksi:* {user_data['total_interactions'] if user_data else 1}\n"
        f"👑 *Status:* {'⭐ SUPER ADMIN' if db.is_super_admin(user.id) else '👑 ADMIN' if db.is_admin(user.id) else '👤 USER'}"
    )
    
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def promo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /promo command - Tampilkan promo"""
    user = update.effective_user
    
    # Simpan user ke database
    db.add_or_update_user(user)
    db.log_interaction(user.id, '/promo')
    
    logger.info(f"🎁 /promo dari {user.first_name} (ID: {user.id})")
    
    # Buat button untuk link
    keyboard = [
        [InlineKeyboardButton("🤖 BOT OFFICIAL", url=URLS['bot_official'])],
        [InlineKeyboardButton("📈 PREDIKSI JITU", url=URLS['prediksi'])],
        [InlineKeyboardButton("📢 CHANNEL WA", url=URLS['channel_wa'])],
        [InlineKeyboardButton("📢 CHANNEL TG", url=URLS['channel_tg'])],
        [InlineKeyboardButton("🟢 KLAIM BONUS", url=URLS['claim'])],
        [InlineKeyboardButton("🔙 KEMBALI KE MENU", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Coba ambil gambar dari database (jadwal pertama yang punya gambar)
    image_url = config.get('images', {}).get('default_promo', "https://i.ibb.co/your-image/promo-banner.jpg")
    posts = db.get_all_posts()
    for post in posts:
        if post.get('image_url'):
            image_url = post['image_url']
            break
    
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
        # Fallback: kirim teks saja
        await update.message.reply_text(
            text=PROMO_TEXT,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=reply_markup
        )

# ==================== ADMIN PANEL ====================

@admin_required
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin command - Dashboard admin"""
    user = update.effective_user
    db.log_interaction(user.id, '/admin')
    
    # Get stats
    user_stats = db.get_user_count()
    posts = db.get_all_posts()
    active_posts = sum(1 for p in posts if p['is_active'])
    
    text = (
        "⚙️ *DASHBOARD ADMIN*\n\n"
        f"👤 *Admin:* {user.first_name}\n"
        f"🆔 *ID:* `{user.id}`\n"
        f"👑 *Level:* {'⭐ SUPER ADMIN' if db.is_super_admin(user.id) else '👑 ADMIN'}\n\n"
        f"📊 *STATISTIK BOT*\n"
        f"• Total User: {user_stats['total']}\n"
        f"• User Baru Hari Ini: {user_stats['today']}\n"
        f"• User Aktif (24h): {user_stats['active']}\n"
        f"• Total Jadwal: {len(posts)}\n"
        f"• Jadwal Aktif: {active_posts}\n\n"
        f"📌 *Menu Admin:*"
    )
    
    keyboard = [
        [InlineKeyboardButton("👥 MANAJEMEN USER", callback_data='admin_users')],
        [InlineKeyboardButton("📢 BROADCAST", callback_data='admin_broadcast')],
        [InlineKeyboardButton("📅 AUTO POST", callback_data='admin_posts')],
        [InlineKeyboardButton("📊 STATISTIK", callback_data='admin_stats')],
    ]
    
    # Tambah menu super admin
    if db.is_super_admin(user.id):
        keyboard.extend([
            [InlineKeyboardButton("👑 KELOLA ADMIN", callback_data='admin_manage_admins')],
            [InlineKeyboardButton("⚙️ PENGATURAN", callback_data='admin_settings')],
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 KEMBALI KE MENU", callback_data='back_to_menu')])
    
    await update.message.reply_text(
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ==================== USER MANAGEMENT ====================

@admin_required
async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /users command - Lihat daftar user"""
    user = update.effective_user
    db.log_interaction(user.id, '/users')
    
    # Parse args
    args = context.args
    page = 1
    if args and args[0].isdigit():
        page = int(args[0])
    
    users = db.get_all_users()
    total = len(users)
    
    # Pagination
    per_page = config.get('limits', {}).get('users_per_page', 10)
    start = (page - 1) * per_page
    end = start + per_page
    current_page_users = users[start:end]
    total_pages = (total + per_page - 1) // per_page
    
    text = f"📋 *DAFTAR USER (Halaman {page}/{total_pages})*\n\n"
    text += f"Total: {total} user\n\n"
    
    for u in current_page_users:
        status = "⛔" if u.get('is_blocked') else "✅"
        admin = "👑" if db.is_admin(u['user_id']) else "👤"
        text += f"{status} {admin} `{u['user_id']}` - {u['first_name']}"
        if u.get('username'):
            text += f" @{u['username']}"
        text += f"\n   📅 {u['joined_date'][:10]}\n"
    
    # Navigation buttons
    keyboard = []
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton("◀️ Sebelumnya", callback_data=f'users_page_{page-1}'))
    if page < total_pages:
        nav_row.append(InlineKeyboardButton("▶️ Selanjutnya", callback_data=f'users_page_{page+1}'))
    if nav_row:
        keyboard.append(nav_row)
    
    keyboard.append([InlineKeyboardButton("🔙 KEMBALI", callback_data='admin_dashboard')])
    
    await update.message.reply_text(
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

@super_admin_required
async def block_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /block command - Blokir user"""
    if not context.args:
        await update.message.reply_text("❌ Gunakan: /block [user_id]")
        return
    
    try:
        target_id = int(context.args[0])
        
        # Cek jangan block super admin
        if target_id in SUPER_ADMINS:
            await update.message.reply_text("❌ Tidak bisa memblokir super admin!")
            return
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET is_blocked = 1 WHERE user_id = ?', (target_id,))
            if cursor.rowcount > 0:
                await update.message.reply_text(f"✅ User `{target_id}` telah diblokir.", parse_mode=ParseMode.MARKDOWN)
                logger.info(f"⛔ User {target_id} diblokir oleh {update.effective_user.id}")
            else:
                await update.message.reply_text(f"❌ User `{target_id}` tidak ditemukan.", parse_mode=ParseMode.MARKDOWN)
    except ValueError:
        await update.message.reply_text("❌ ID user harus berupa angka!")

@super_admin_required
async def unblock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /unblock command - Buka blokir user"""
    if not context.args:
        await update.message.reply_text("❌ Gunakan: /unblock [user_id]")
        return
    
    try:
        target_id = int(context.args[0])
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET is_blocked = 0 WHERE user_id = ?', (target_id,))
            if cursor.rowcount > 0:
                await update.message.reply_text(f"✅ User `{target_id}` telah dibuka blokirnya.", parse_mode=ParseMode.MARKDOWN)
                logger.info(f"✅ User {target_id} dibuka blokirnya oleh {update.effective_user.id}")
            else:
                await update.message.reply_text(f"❌ User `{target_id}` tidak ditemukan.", parse_mode=ParseMode.MARKDOWN)
    except ValueError:
        await update.message.reply_text("❌ ID user harus berupa angka!")

# ==================== ADMIN MANAGEMENT ====================

@super_admin_required
async def admins_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admins command - Kelola admin"""
    user = update.effective_user
    db.log_interaction(user.id, '/admins')
    
    admins = db.get_all_admins()
    
    text = "👑 *MANAJEMEN ADMIN*\n\n"
    text += f"Total Admin: {len(admins)}\n\n"
    
    for admin in admins:
        super_star = "⭐" if admin['is_super'] else "👑"
        name = admin.get('first_name') or f"User {admin['user_id']}"
        username = f"@{admin['username']}" if admin.get('username') else ""
        text += f"{super_star} `{admin['user_id']}` - {name} {username}\n"
        text += f"   📅 Added: {admin['added_date'][:10]}\n\n"
    
    text += "\nPilih menu di bawah:"
    
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

# ==================== BROADCAST SYSTEM ====================

@admin_required
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /broadcast command - Kirim broadcast"""
    user = update.effective_user
    db.log_interaction(user.id, '/broadcast')
    
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

# ==================== AUTO POST MANAGEMENT ====================

@admin_required
async def posts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /posts command - Kelola auto post"""
    user = update.effective_user
    db.log_interaction(user.id, '/posts')
    
    posts = db.get_all_posts()
    
    text = "📅 *MANAJEMEN AUTO POST*\n\n"
    
    if posts:
        for post in posts:
            status = "✅ AKTIF" if post['is_active'] else "❌ NONAKTIF"
            text += f"🆔 *{post['post_id']}* | {post['time']} | {status}\n"
            preview = post['text'][:50] + ('...' if len(post['text']) > 50 else '')
            text += f"   `{preview}`\n"
            if post.get('image_url'):
                text += f"   📷 Ada Gambar\n"
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

# ==================== STATISTICS ====================

@admin_required
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command - Lihat statistik lengkap"""
    user = update.effective_user
    db.log_interaction(user.id, '/stats')
    
    user_stats = db.get_user_count()
    posts = db.get_all_posts()
    broadcasts = db.get_all_broadcasts(5)
    
    # Hitung interaksi hari ini
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as today FROM user_interactions WHERE date(timestamp) = date("now")')
        interactions_today = cursor.fetchone()[0]
    
    text = (
        "📊 *STATISTIK BOT LENGKAP*\n\n"
        "👥 *USER STATISTICS*\n"
        f"• Total User: {user_stats['total']}\n"
        f"• User Baru Hari Ini: {user_stats['today']}\n"
        f"• User Aktif (24h): {user_stats['active']}\n"
        f"• Interaksi Hari Ini: {interactions_today}\n\n"
        "📅 *AUTO POST*\n"
        f"• Total Jadwal: {len(posts)}\n"
        f"• Jadwal Aktif: {sum(1 for p in posts if p['is_active'])}\n\n"
        "📢 *BROADCAST TERAKHIR*\n"
    )
    
    if broadcasts:
        for b in broadcasts[:3]:
            status_emoji = {
                'draft': '📝', 'scheduled': '⏰', 
                'sending': '📤', 'sent': '✅', 'cancelled': '❌'
            }.get(b['status'], '📋')
            text += f"{status_emoji} {b['created_at'][:10]} - {b['success_count']}/{b['total_recipients'] or 0} sukses\n"
    else:
        text += "Belum ada broadcast\n"
    
    text += f"\n⚙️ *VERSI BOT*\n• Ultimate Edition v2.0"
    
    keyboard = [[InlineKeyboardButton("🔙 KEMBALI", callback_data='admin_dashboard')]]
    
    await update.message.reply_text(
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ==================== SETTINGS ====================

@super_admin_required
async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /settings command - Pengaturan bot"""
    user = update.effective_user
    db.log_interaction(user.id, '/settings')
    
    settings = [
        ('welcome_enabled', 'Welcome Message'),
        ('auto_post_enabled', 'Auto Post'),
        ('broadcast_delay', 'Delay Broadcast (detik)'),
        ('max_broadcast_per_day', 'Max Broadcast/hari'),
        ('bot_name', 'Nama Bot'),
        ('support_contact', 'Kontak Support'),
    ]
    
    text = "⚙️ *PENGATURAN BOT*\n\n"
    
    for key, label in settings:
        value = db.get_setting(key)
        text += f"• *{label}:* `{value}`\n"
    
    text += "\nUntuk mengubah: /set [key] [value]"
    
    keyboard = [[InlineKeyboardButton("🔙 KEMBALI", callback_data='admin_dashboard')]]
    
    await update.message.reply_text(
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

@super_admin_required
async def set_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /set command - Ubah setting"""
    if len(context.args) < 2:
        await update.message.reply_text("❌ Gunakan: /set [key] [value]")
        return
    
    key = context.args[0]
    value = ' '.join(context.args[1:])
    
    if db.update_setting(key, value, update.effective_user.id):
        await update.message.reply_text(f"✅ Setting `{key}` diubah menjadi `{value}`", parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(f"❌ Gagal mengubah setting `{key}`", parse_mode=ParseMode.MARKDOWN)

# ==================== BUTTON HANDLERS ====================

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all button callbacks"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    data = query.data
    
    logger.info(f"🔘 Button {data} diklik oleh {user.first_name} (ID: {user.id})")
    
    try:
        # ========== USER BUTTONS ==========
        if data == "login":
            text = "🔐 *Link Login*\n\nKlik tombol di bawah untuk login:"
            keyboard = [[InlineKeyboardButton("🔐 LOGIN SEKARANG", url=URLS['login'])]]
            await query.message.reply_text(
                text=text, 
                parse_mode=ParseMode.MARKDOWN, 
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            await query.delete_message()
        
        elif data == "daftar":
            text = "📝 *Link Daftar*\n\nKlik tombol di bawah untuk mendaftar:"
            keyboard = [[InlineKeyboardButton("📝 DAFTAR SEKARANG", url=URLS['daftar'])]]
            await query.message.reply_text(
                text=text, 
                parse_mode=ParseMode.MARKDOWN, 
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            await query.delete_message()
        
        elif data == "claim":
            text = "🎁 *Claim Event Parlay*\n\nKlik tombol di bawah untuk klaim bonus:"
            keyboard = [[InlineKeyboardButton("🎁 CLAIM BONUS", url=URLS['claim'])]]
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
            # Kembali ke menu utama
            await start_command(update, context)
        
        # ========== ADMIN BUTTONS ==========
        elif data == "admin_dashboard":
            if not db.is_admin(user.id):
                await query.message.reply_text("❌ Akses ditolak")
                return
            
            user_stats = db.get_user_count()
            posts = db.get_all_posts()
            active_posts = sum(1 for p in posts if p['is_active'])
            
            text = (
                "⚙️ *DASHBOARD ADMIN*\n\n"
                f"👤 *Admin:* {user.first_name}\n"
                f"🆔 *ID:* `{user.id}`\n"
                f"👑 *Level:* {'⭐ SUPER ADMIN' if db.is_super_admin(user.id) else '👑 ADMIN'}\n\n"
                f"📊 *STATISTIK*\n"
                f"• Total User: {user_stats['total']}\n"
                f"• User Baru Hari Ini: {user_stats['today']}\n"
                f"• User Aktif (24h): {user_stats['active']}\n"
                f"• Total Jadwal: {len(posts)}\n"
                f"• Jadwal Aktif: {active_posts}\n\n"
                f"📌 *Menu Admin:*"
            )
            
            keyboard = [
                [InlineKeyboardButton("👥 MANAJEMEN USER", callback_data='admin_users')],
                [InlineKeyboardButton("📢 BROADCAST", callback_data='admin_broadcast')],
                [InlineKeyboardButton("📅 AUTO POST", callback_data='admin_posts')],
                [InlineKeyboardButton("📊 STATISTIK", callback_data='admin_stats')],
            ]
            
            if db.is_super_admin(user.id):
                keyboard.extend([
                    [InlineKeyboardButton("👑 KELOLA ADMIN", callback_data='admin_manage_admins')],
                    [InlineKeyboardButton("⚙️ PENGATURAN", callback_data='admin_settings')],
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
            
            users = db.get_all_users()
            total = len(users)
            
            text = f"👥 *MANAJEMEN USER*\n\nTotal User: {total}\n\nPilih opsi di bawah:"
            
            keyboard = [
                [InlineKeyboardButton("📋 LIHAT SEMUA USER", callback_data='users_page_1')],
                [InlineKeyboardButton("📊 STATISTIK USER", callback_data='user_stats')],
            ]
            
            if db.is_super_admin(user.id):
                keyboard.append([InlineKeyboardButton("⛔ BLOKIR USER", callback_data='user_block')])
                keyboard.append([InlineKeyboardButton("✅ BUKA BLOKIR", callback_data='user_unblock')])
            
            keyboard.append([InlineKeyboardButton("🔙 KEMBALI", callback_data='admin_dashboard')])
            
            await query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        elif data == "admin_broadcast":
            if not db.is_admin(user.id):
                return
            
            text = (
                "📢 *SISTEM BROADCAST*\n\n"
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
            
            posts = db.get_all_posts()
            
            text = "📅 *MANAJEMEN AUTO POST*\n\n"
            
            if posts:
                for post in posts[:5]:
                    status = "✅" if post['is_active'] else "❌"
                    text += f"{status} ID {post['post_id']}: {post['time']}\n"
                    preview = post['text'][:30] + '...' if len(post['text']) > 30 else post['text']
                    text += f"   `{preview}`\n"
                if len(posts) > 5:
                    text += f"\n...dan {len(posts)-5} jadwal lainnya\n"
            else:
                text += "Belum ada jadwal.\n"
            
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
            
            user_stats = db.get_user_count()
            posts = db.get_all_posts()
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM user_interactions WHERE date(timestamp) = date("now")')
                interactions_today = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM broadcast_messages WHERE status = "sent"')
                total_broadcasts = cursor.fetchone()[0]
            
            text = (
                "📊 *STATISTIK BOT*\n\n"
                "👥 *USER*\n"
                f"• Total: {user_stats['total']}\n"
                f"• Hari Ini: {user_stats['today']}\n"
                f"• Aktif 24h: {user_stats['active']}\n"
                f"• Interaksi Hari Ini: {interactions_today}\n\n"
                "📅 *AUTO POST*\n"
                f"• Total Jadwal: {len(posts)}\n"
                f"• Aktif: {sum(1 for p in posts if p['is_active'])}\n\n"
                "📢 *BROADCAST*\n"
                f"• Total Broadcast: {total_broadcasts}\n"
            )
            
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
                super_star = "⭐" if admin['is_super'] else "👑"
                name = admin.get('first_name') or f"User {admin['user_id']}"
                text += f"{super_star} `{admin['user_id']}` - {name}\n"
            
            if len(admins) > 5:
                text += f"\n...dan {len(admins)-5} lainnya\n"
            
            text += "\nPilih menu:"
            
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
            
            settings = [
                ('welcome_enabled', 'Welcome'),
                ('auto_post_enabled', 'Auto Post'),
                ('broadcast_delay', 'Delay'),
                ('max_broadcast_per_day', 'Max BC'),
                ('bot_name', 'Nama Bot'),
            ]
            
            text = "⚙️ *PENGATURAN*\n\n"
            for key, label in settings:
                value = db.get_setting(key)
                text += f"• {label}: `{value}`\n"
            
            text += "\nGunakan /set [key] [value] untuk mengubah"
            
            keyboard = [[InlineKeyboardButton("🔙 KEMBALI", callback_data='admin_dashboard')]]
            
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
            users = db.get_all_users()
            total = len(users)
            
            per_page = config.get('limits', {}).get('users_per_page', 10)
            start = (page - 1) * per_page
            end = start + per_page
            current_page_users = users[start:end]
            total_pages = (total + per_page - 1) // per_page
            
            text = f"📋 *DAFTAR USER (Halaman {page}/{total_pages})*\n\n"
            
            for u in current_page_users:
                status = "⛔" if u.get('is_blocked') else "✅"
                admin = "👑" if db.is_admin(u['user_id']) else "👤"
                text += f"{status} {admin} `{u['user_id']}` - {u['first_name']}"
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
        
        # ========== BROADCAST BUTTONS ==========
        elif data == "broadcast_text":
            if not db.is_admin(user.id):
                return
            
            context.user_data['broadcast_step'] = 'text'
            await query.message.edit_text(
                "📝 *BROADCAST TEKS*\n\n"
                "Silakan kirim pesan teks yang ingin di-broadcast.\n\n"
                "Format *Markdown* didukung.\n"
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
                        'sending': '📤', 'sent': '✅', 'cancelled': '❌'
                    }.get(b['status'], '📋')
                    creator = b.get('creator_name') or f"User {b['created_by']}"
                    text += f"{status_emoji} {b['created_at'][:16]} - {creator}\n"
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
            
            context.user_data['post_step'] = 'time'
            await query.message.edit_text(
                "➕ *TAMBAH JADWAL AUTO POST*\n\n"
                "Langkah 1/4: Masukkan waktu (HH:MM)\n"
                "Contoh: `14:30`\n\n"
                "Ketik *batal* untuk membatalkan.",
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif data == "posts_list":
            if not db.is_admin(user.id):
                return
            
            posts = db.get_all_posts()
            
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
                    super_star = "⭐" if admin['is_super'] else "👑"
                    name = admin.get('first_name') or f"User {admin['user_id']}"
                    username = f"@{admin['username']}" if admin.get('username') else ""
                    text += f"{super_star} `{admin['user_id']}` - {name} {username}\n"
                    text += f"   📅 {admin['added_date'][:10]}\n\n"
            
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
        
        # ========== USER STATS ==========
        elif data == "user_stats":
            if not db.is_admin(user.id):
                return
            
            user_stats = db.get_user_count()
            
            text = (
                "📊 *STATISTIK USER*\n\n"
                f"• Total User: {user_stats['total']}\n"
                f"• User Baru Hari Ini: {user_stats['today']}\n"
                f"• User Aktif 24 Jam: {user_stats['active']}\n"
            )
            
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
        
        elif data == "user_unblock":
            if not db.is_super_admin(user.id):
                return
            
            context.user_data['admin_action'] = 'unblock'
            await query.message.edit_text(
                "✅ *BUKA BLOKIR USER*\n\n"
                "Masukkan User ID yang ingin dibuka blokirnya:\n\n"
                "Ketik *batal* untuk membatalkan.",
                parse_mode=ParseMode.MARKDOWN
            )
        
        # ========== CONFIRM BROADCAST ==========
        elif data.startswith('confirm_broadcast_'):
            if not db.is_admin(user.id):
                return
            
            broadcast_id = int(data.split('_')[2])
            
            # Ambil data broadcast
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
            
            # Kirim broadcast di background
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
        logger.error(f"❌ Error di button_callback: {e}")
        await query.message.reply_text(
            "❌ Terjadi kesalahan. Silakan coba lagi nanti."
        )

# ==================== FUNGSI KIRIM PROMO ====================

async def send_promo(message, context):
    """Kirim promo dengan gambar"""
    try:
        # Buat button untuk link
        keyboard = [
            [InlineKeyboardButton("🤖 BOT OFFICIAL", url=URLS['bot_official'])],
            [InlineKeyboardButton("📈 PREDIKSI JITU", url=URLS['prediksi'])],
            [InlineKeyboardButton("📢 CHANNEL WA", url=URLS['channel_wa'])],
            [InlineKeyboardButton("📢 CHANNEL TG", url=URLS['channel_tg'])],
            [InlineKeyboardButton("🟢 KLAIM BONUS", url=URLS['claim'])],
            [InlineKeyboardButton("🔙 KEMBALI KE MENU", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Coba ambil gambar dari database
        image_url = config.get('images', {}).get('default_promo', "https://i.ibb.co/your-image/promo-banner.jpg")
        
        try:
            await message.reply_photo(
                photo=image_url,
                caption=PROMO_TEXT,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            logger.info("✅ Promo dengan gambar terkirim")
        except Exception as e:
            logger.warning(f"⚠️ Gagal kirim gambar: {e}, kirim teks saja")
            await message.reply_text(
                text=PROMO_TEXT,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
                reply_markup=reply_markup
            )
    except Exception as e:
        logger.error(f"❌ Gagal kirim promo: {e}")

# ==================== MESSAGE HANDLER ====================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all text messages"""
    user = update.effective_user
    text = update.message.text
    
    # Simpan user
    db.add_or_update_user(user)
    
    # Cek apakah user di-block
    user_data = db.get_user(user.id)
    if user_data and user_data.get('is_blocked'):
        return
    
    # ===== BROADCAST FLOW =====
    if 'broadcast_step' in context.user_data:
        step = context.user_data['broadcast_step']
        
        if text.lower() == 'batal':
            del context.user_data['broadcast_step']
            await update.message.reply_text("✅ Broadcast dibatalkan.")
            return
        
        if step == 'text':
            # Simpan teks broadcast
            broadcast_id = db.create_broadcast(
                created_by=user.id,
                message_text=text,
                message_type='text'
            )
            
            # Kirim konfirmasi
            keyboard = [
                [
                    InlineKeyboardButton("✅ KIRIM SEKARANG", callback_data=f'confirm_broadcast_{broadcast_id}'),
                    InlineKeyboardButton("❌ BATAL", callback_data='admin_broadcast')
                ]
            ]
            
            await update.message.reply_text(
                "📢 *KONFIRMASI BROADCAST*\n\n"
                f"Teks:\n{text}\n\n"
                "Kirim sekarang?",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
            del context.user_data['broadcast_step']
        
        elif step == 'waiting_image':
            # Catat bahwa ini adalah gambar (seharusnya file_id, tapi untuk contoh)
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
                # Validasi waktu
                hour, minute = map(int, text.split(':'))
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    context.user_data['post_time'] = text
                    context.user_data['post_step'] = 'text'
                    await update.message.reply_text(
                        "Langkah 2/4: Masukkan teks yang ingin dikirim:"
                    )
                else:
                    await update.message.reply_text("❌ Format waktu salah! Gunakan HH:MM (00-23:00-59)")
            except:
                await update.message.reply_text("❌ Format waktu salah! Gunakan HH:MM")
        
        elif step == 'text':
            context.user_data['post_text'] = text
            context.user_data['post_step'] = 'image'
            await update.message.reply_text(
                "Langkah 3/4: Masukkan URL gambar (atau ketik - untuk tanpa gambar):"
            )
        
        elif step == 'image':
            image_url = None if text == '-' else text
            context.user_data['post_image'] = image_url
            context.user_data['post_step'] = 'button'
            await update.message.reply_text(
                "Langkah 4/4: Masukkan teks tombol (atau ketik - untuk tanpa tombol):"
            )
        
        elif step == 'button':
            if text != '-':
                context.user_data['post_button_text'] = text
                context.user_data['post_step'] = 'button_url'
                await update.message.reply_text(
                    "Masukkan URL untuk tombol tersebut:"
                )
            else:
                # Simpan tanpa tombol
                post_id = db.add_post(
                    time_str=context.user_data['post_time'],
                    text=context.user_data['post_text'],
                    image_url=context.user_data.get('post_image'),
                    created_by=user.id
                )
                
                await update.message.reply_text(f"✅ Jadwal ID {post_id} berhasil ditambahkan!")
                del context.user_data['post_step']
        
        elif step == 'button_url':
            # Simpan dengan tombol
            post_id = db.add_post(
                time_str=context.user_data['post_time'],
                text=context.user_data['post_text'],
                image_url=context.user_data.get('post_image'),
                button_text=context.user_data.get('post_button_text'),
                button_url=text,
                created_by=user.id
            )
            
            await update.message.reply_text(f"✅ Jadwal ID {post_id} berhasil ditambahkan!")
            del context.user_data['post_step']
        
        return
    
    # ===== POST ACTION FLOW (edit/delete/toggle) =====
    if 'post_action' in context.user_data:
        action = context.user_data['post_action']
        
        if text.lower() == 'batal':
            del context.user_data['post_action']
            await update.message.reply_text("✅ Operasi dibatalkan.")
            return
        
        try:
            post_id = int(text)
            
            if action == 'edit':
                # Ambil data post
                post = db.get_post(post_id)
                if not post:
                    await update.message.reply_text(f"❌ Jadwal ID {post_id} tidak ditemukan.")
                    del context.user_data['post_action']
                    return
                
                context.user_data['edit_post_id'] = post_id
                context.user_data['post_step'] = 'time'
                await update.message.reply_text(
                    f"✏️ *EDIT JADWAL ID {post_id}*\n\n"
                    f"Data saat ini:\n"
                    f"Waktu: {post['time']}\n"
                    f"Teks: {post['text'][:50]}...\n\n"
                    f"Masukkan waktu baru (HH:MM):",
                    parse_mode=ParseMode.MARKDOWN
                )
                del context.user_data['post_action']
            
            elif action == 'delete':
                if db.delete_post(post_id):
                    await update.message.reply_text(f"✅ Jadwal ID {post_id} telah dihapus.")
                else:
                    await update.message.reply_text(f"❌ Gagal menghapus jadwal ID {post_id}.")
                del context.user_data['post_action']
            
            elif action == 'toggle':
                if db.toggle_post(post_id):
                    post = db.get_post(post_id)
                    status = "diaktifkan" if post['is_active'] else "dinonaktifkan"
                    await update.message.reply_text(f"✅ Jadwal ID {post_id} telah {status}.")
                else:
                    await update.message.reply_text(f"❌ Gagal mengubah status jadwal ID {post_id}.")
                del context.user_data['post_action']
        
        except ValueError:
            await update.message.reply_text("❌ ID harus berupa angka!")
        
        return
    
    # ===== ADMIN ACTION FLOW (block/unblock) =====
    if 'admin_action' in context.user_data:
        action = context.user_data['admin_action']
        
        if text.lower() == 'batal':
            del context.user_data['admin_action']
            await update.message.reply_text("✅ Operasi dibatalkan.")
            return
        
        try:
            target_id = int(text)
            
            if action == 'block':
                if target_id in SUPER_ADMINS:
                    await update.message.reply_text("❌ Tidak bisa memblokir super admin!")
                else:
                    with db.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute('UPDATE users SET is_blocked = 1 WHERE user_id = ?', (target_id,))
                        if cursor.rowcount > 0:
                            await update.message.reply_text(f"✅ User `{target_id}` telah diblokir.", parse_mode=ParseMode.MARKDOWN)
                        else:
                            await update.message.reply_text(f"❌ User `{target_id}` tidak ditemukan.", parse_mode=ParseMode.MARKDOWN)
            
            elif action == 'unblock':
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE users SET is_blocked = 0 WHERE user_id = ?', (target_id,))
                    if cursor.rowcount > 0:
                        await update.message.reply_text(f"✅ User `{target_id}` telah dibuka blokirnya.", parse_mode=ParseMode.MARKDOWN)
                    else:
                        await update.message.reply_text(f"❌ User `{target_id}` tidak ditemukan.", parse_mode=ParseMode.MARKDOWN)
            
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
                
                # Cek user di database
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
                
                # Dapatkan username
                user_data = db.get_user(target_id)
                username = user_data['username'] if user_data else None
                
                if db.add_admin(target_id, user.id, username):
                    await update.message.reply_text(f"✅ User `{target_id}` sekarang adalah admin!", parse_mode=ParseMode.MARKDOWN)
                    logger.info(f"👑 Admin baru: {target_id} ditambahkan oleh {user.id}")
                else:
                    await update.message.reply_text("❌ Gagal menambahkan admin.")
            else:
                await update.message.reply_text("✅ Penambahan admin dibatalkan.")
            
            del context.user_data['admin_step']
        
        elif step == 'remove_id':
            try:
                target_id = int(text)
                
                if target_id in SUPER_ADMINS:
                    await update.message.reply_text("❌ Tidak bisa menghapus super admin!")
                    del context.user_data['admin_step']
                    return
                
                if db.remove_admin(target_id, user.id):
                    await update.message.reply_text(f"✅ Admin `{target_id}` telah dihapus.", parse_mode=ParseMode.MARKDOWN)
                    logger.info(f"👑 Admin {target_id} dihapus oleh {user.id}")
                else:
                    await update.message.reply_text(f"❌ Gagal menghapus admin `{target_id}`", parse_mode=ParseMode.MARKDOWN)
                
                del context.user_data['admin_step']
            except ValueError:
                await update.message.reply_text("❌ User ID harus berupa angka!")

# ==================== WELCOME NEW MEMBER ====================

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sapa member baru di channel"""
    if not update.channel_post or not update.channel_post.new_chat_members:
        return
    
    message = update.channel_post
    chat = update.effective_chat
    
    if chat.id != CHANNEL_ID:
        return
    
    if db.get_setting('welcome_enabled') != 'true':
        return
    
    logger.info(f"🎉 MEMBER BARU DETEKSI DI CHANNEL!")
    
    for new_member in message.new_chat_members:
        if new_member.is_bot:
            continue
        
        # Simpan ke database
        db.add_or_update_user(new_member)
        
        mention = f"[{new_member.first_name}](tg://user?id={new_member.id})"
        
        welcome_text = (
            f"🎉 *SELAMAT DATANG* 🎉\n\n"
            f"Halo {mention}!\n"
            f"Selamat bergabung di *{db.get_setting('bot_name')} Official Channel*!\n\n"
            f"📌 *Link Penting:*\n"
            f"• [🤖 BOT OFFICIAL]({URLS['bot_official']})\n"
            f"• [🟢 WA KLAIM BONUS]({URLS['claim']})\n"
            f"• [📢 CHANNEL WA]({URLS['channel_wa']})\n"
            f"• [📢 CHANNEL TG]({URLS['channel_tg']})\n\n"
            f"🔥 *GasPoll!* 🔥"
        )
        
        try:
            await context.bot.send_message(
                chat_id=chat.id,
                text=welcome_text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
            logger.info(f"✅ Welcome terkirim untuk {new_member.first_name}")
        except Exception as e:
            logger.error(f"❌ Gagal kirim welcome: {e}")

# ==================== TEST CHANNEL ====================

async def test_channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test kirim ke channel"""
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

async def check_auto_posts(context: ContextTypes.DEFAULT_TYPE):
    """Job untuk mengecek dan mengirim auto post"""
    if db.get_setting('auto_post_enabled') == 'true':
        await scheduler.check_and_send_posts(context)

async def check_scheduled_broadcasts(context: ContextTypes.DEFAULT_TYPE):
    """Job untuk mengecek broadcast terjadwal"""
    pending = db.get_pending_broadcasts()
    
    for broadcast in pending:
        # Kirim broadcast
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
    """Fungsi setelah bot start"""
    logger.info("=" * 70)
    logger.info("🤖 BOT BOLAPELANGI 2 ULTIMATE EDITION READY!")
    logger.info("=" * 70)
    
    try:
        bot_info = await application.bot.get_me()
        logger.info(f"✅ Bot: @{bot_info.username}")
        logger.info(f"✅ Channel ID: {CHANNEL_ID}")
        
        # Buat folder yang diperlukan
        os.makedirs('data', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        os.makedirs('backups', exist_ok=True)
        logger.info("✅ Created required folders")
        
        # Job untuk auto post (setiap menit)
        job_queue = application.job_queue
        if job_queue:
            job_queue.run_repeating(check_auto_posts, interval=60, first=10)
            
            # Job untuk broadcast terjadwal (setiap 5 menit)
            job_queue.run_repeating(check_scheduled_broadcasts, interval=300, first=30)
        
        # Kirim startup ke channel
        try:
            await application.bot.send_message(
                chat_id=CHANNEL_ID,
                text="🤖 *Bot Ultimate Edition Aktif*\n\n✅ Sistem auto post & broadcast siap!",
                parse_mode=ParseMode.MARKDOWN
            )
            logger.info("✅ Pesan startup terkirim ke channel")
        except Exception as e:
            logger.error(f"❌ Tidak bisa kirim ke channel: {e}")
        
        logger.info(f"✅ Total user di database: {db.get_user_count()['total']}")
        logger.info(f"✅ Total admin: {len(db.get_all_admins())}")
        logger.info(f"✅ Total auto posts: {len(db.get_all_posts())}")
        
    except Exception as e:
        logger.error(f"❌ Gagal inisialisasi: {e}")

# ==================== MAIN FUNCTION ====================

def main():
    """Main function"""
    
    print("=" * 70)
    print("🤖 BOT BOLAPELANGI 2 - ULTIMATE EDITION")
    print("=" * 70)
    print("🔧 FITUR SUPER LENGKAP:")
    print("   ✅ Auto Welcome Member")
    print("   ✅ Auto Post Terjadwal")
    print("   ✅ Broadcast System")
    print("   ✅ Database SQLite")
    print("   ✅ Admin Management")
    print("   ✅ User Tracking")
    print("   ✅ Super Admin Protection")
    print("   ✅ Statistics")
    print("=" * 70)
    
    if not BOT_TOKEN or len(BOT_TOKEN) < 40:
        print("❌ ERROR: BOT_TOKEN tidak valid!")
        sys.exit(1)
    
    print(f"✅ SUPER ADMIN TERDAFTAR: {SUPER_ADMINS}")
    
    try:
        application = (
            Application.builder()
            .token(BOT_TOKEN)
            .post_init(post_init)
            .concurrent_updates(True)
            .build()
        )
        print("✅ Application berhasil dibuat")
    except Exception as e:
        print(f"❌ Gagal: {e}")
        sys.exit(1)
    
    # Command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("info", info_command))
    application.add_handler(CommandHandler("promo", promo_command))
    application.add_handler(CommandHandler("test_channel", test_channel_command))
    
    # Admin commands
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("users", users_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("posts", posts_command))
    application.add_handler(CommandHandler("stats", stats_command))
    
    # Super admin commands
    application.add_handler(CommandHandler("admins", admins_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CommandHandler("set", set_command))
    application.add_handler(CommandHandler("block", block_command))
    application.add_handler(CommandHandler("unblock", unblock_command))
    
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
    
    print("=" * 70)
    print("📢 BOT RUNNING - ULTIMATE EDITION")
    print("📢 Fitur: Auto Welcome | Auto Post | Broadcast | Admin Panel")
    print("📢 Database: SQLite dengan semua tracking")
    print("📢 Super Admin: @Bolapelangi2 & @bolapelangi_2")
    print("=" * 70)
    sys.stdout.flush()
    
    # Jalankan bot
    application.run_polling(
        allowed_updates=["message", "channel_post", "callback_query"],
        drop_pending_updates=True
    )

if __name__ == "__main__":
    main()
