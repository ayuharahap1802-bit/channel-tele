"""
TELEGRAM WELCOME BOT - BOLAPELANGI 2
VERSI: FINAL DENGAN AUTO POST SCHEDULER
Fitur: Auto welcome + Auto post terjadwal + Setting via personal chat
Created for: @bolapelangi2_bot
"""

import os
import logging
import sys
import asyncio
import json
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode

# ==================== KONFIGURASI DARI ENVIRONMENT ====================

print("=" * 60)
print("🔍 MEMULAI BOT BOLAPELANGI 2 DENGAN AUTO POST...")
print("=" * 60)

# Baca dari environment variable Railway
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID_STR = os.environ.get("CHANNEL_ID")

print(f"🔍 BOT_TOKEN: {'ADA' if BOT_TOKEN else 'TIDAK ADA'}")
print(f"🔍 CHANNEL_ID: {CHANNEL_ID_STR}")

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

# ==================== KONFIGURASI LOGGING ====================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ==================== DATA STORAGE ====================

class AutoPostManager:
    """Manager untuk menyimpan dan mengelola jadwal auto post"""
    
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
                        "text": PROMO_TEXT,  # Pakai promo default
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

# ==================== INISIALISASI MANAGER ====================

post_manager = AutoPostManager()

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
🤖 [BOT OFFICIAL](https://t.me/bolapelangi2_bot)
📈 [PREDIKSI JITU](https://bopel2.vip/ChannelWA-Jadwal-Prediksi)
📢 [CHANNEL WHATSAPP](https://bopel2.vip/Channel-Whatsapp)
📢 [CHANNEL TELEGRAM](https://bopel2.vip/Channel-Telegram)
🟢 [KLAIM BONUS](https://bopel2.link/wa)

📌 *Catatan:* 1x/hari, no IP sama, no safety bet
🚀 *GASPOLL TERUS BOSKU!*
"""

# ==================== FUNGSI AUTO POST ====================

async def send_scheduled_post(context: ContextTypes.DEFAULT_TYPE, post: Dict):
    """Kirim postingan terjadwal ke channel"""
    try:
        logger.info(f"📢 Mengirim auto post jadwal {post.get('id')} - {post.get('time')}")
        
        # Buat button default untuk promo
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
            # Kirim teks saja
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=post['text'],
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
                reply_markup=reply_markup
            )
            logger.info(f"✅ Auto post {post.get('id')} terkirim")
        
        # Jadwalkan pengiriman berikutnya
        await schedule_next_run(context)
        
    except Exception as e:
        logger.error(f"❌ Gagal auto post: {e}")

async def check_scheduled_posts(context: ContextTypes.DEFAULT_TYPE):
    """Cek dan kirim postingan yang waktunya sudah tiba"""
    due_posts = post_manager.get_posts_due_now()
    
    if due_posts:
        logger.info(f"⏰ Menemukan {len(due_posts)} jadwal yang harus dikirim")
        for post in due_posts:
            await send_scheduled_post(context, post)
    else:
        # Tidak ada jadwal yang harus dikirim sekarang
        pass

async def schedule_next_run(context: ContextTypes.DEFAULT_TYPE):
    """Jadwalkan pengecekan berikutnya"""
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
            check_scheduled_posts,
            when=delay,
            name='check_posts'
        )
        logger.info(f"📅 Next check scheduled at {next_run.strftime('%Y-%m-%d %H:%M:%S')} (in {delay/60:.1f} minutes)")
    else:
        logger.warning("⚠️ Tidak ada jadwal aktif")

# ==================== COMMAND ADMIN ====================

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command untuk mengatur auto post - HANYA UNTUK ADMIN TERTENTU"""
    user = update.effective_user
    
    # Authorisasi user (bisa ditambah manual)
    # Untuk demo, izinkan semua user dulu
    # Tapi nanti bisa diubah dengan mengecek user_id tertentu
    
    logger.info(f"👑 /admin digunakan oleh {user.first_name} (ID: {user.id})")
    
    # Tambahkan user ke authorized list
    post_manager.authorized_users.add(user.id)
    
    text = (
        "🔧 *PANEL ADMIN AUTO POST*\n\n"
        "Kelola jadwal posting otomatis ke channel.\n\n"
        "📋 *Menu:*/n"
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
    """Tampilkan semua jadwal auto post"""
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
        # Tampilkan preview teks (max 50 chars)
        preview = post.get('text', '')[:50] + ('...' if len(post.get('text', '')) > 50 else '')
        text += f"   `{preview}`\n\n"
    
    text += "\nGunakan /edit_jadwal [id] untuk mengedit."
    
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def tambah_jadwal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mulai proses tambah jadwal"""
    user = update.effective_user
    
    if user.id not in post_manager.authorized_users:
        await update.message.reply_text("❌ Anda tidak diizinkan menggunakan perintah ini.")
        return
    
    # Set state untuk input
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
    """Mulai proses edit jadwal"""
    user = update.effective_user
    
    if user.id not in post_manager.authorized_users:
        await update.message.reply_text("❌ Anda tidak diizinkan menggunakan perintah ini.")
        return
    
    # Cek apakah ada argumen ID
    args = context.args
    if not args:
        await update.message.reply_text("❌ Gunakan: /edit_jadwal [id]\nContoh: /edit_jadwal 1")
        return
    
    post_id = args[0]
    if post_id not in post_manager.posts:
        await update.message.reply_text(f"❌ Jadwal dengan ID {post_id} tidak ditemukan.")
        return
    
    # Set state untuk input
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
    """Hapus jadwal"""
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
    
    # Konfirmasi hapus
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
    """Aktifkan jadwal"""
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
    
    # Reschedule
    await schedule_next_run(context)

async def nonaktifkan_jadwal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Nonaktifkan jadwal"""
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
    
    # Reschedule
    await schedule_next_run(context)

# ==================== MESSAGE HANDLER UNTUK INPUT ====================

async def handle_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle input dari user (untuk proses tambah/edit)"""
    user = update.effective_user
    text = update.message.text
    
    # Cek apakah user sedang dalam proses input
    if user.id not in post_manager.pending_input:
        return
    
    state = post_manager.pending_input[user.id]
    
    # Cek batal
    if text.lower() == 'batal':
        del post_manager.pending_input[user.id]
        await update.message.reply_text("✅ Proses dibatalkan.")
        return
    
    # Proses berdasarkan action
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
        # Validasi format waktu
        try:
            hour, minute = map(int, text.split(':'))
            if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                raise ValueError
            
            # Simpan waktu
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
        # Simpan teks
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
        # Simpan URL gambar
        image_url = None if text == '-' else text
        state['image_url'] = image_url
        state['step'] = 'confirm'
        
        # Tampilkan konfirmasi
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
            # Cari ID baru
            new_id = str(len(post_manager.posts) + 1)
            while new_id in post_manager.posts:
                new_id = str(int(new_id) + 1)
            
            # Simpan jadwal
            post_manager.add_post(
                post_id=new_id,
                time_str=state['time'],
                text=state['text'],
                image_url=state['image_url']
            )
            
            del post_manager.pending_input[user.id]
            await update.message.reply_text(f"✅ Jadwal ID {new_id} berhasil ditambahkan!")
            
            # Reschedule
            await schedule_next_run(context)
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
            
            # Reschedule
            await schedule_next_run(context)
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
        
        # Reschedule
        await schedule_next_run(context)
    elif text == 'tidak':
        del post_manager.pending_input[user.id]
        await update.message.reply_text("✅ Penghapusan dibatalkan")
    else:
        await update.message.reply_text("❌ Ketik *ya* atau *tidak*", parse_mode=ParseMode.MARKDOWN)

# ==================== BUTTON HANDLERS ====================

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    data = query.data
    
    logger.info(f"🔘 Button {data} diklik oleh {user.first_name}")
    
    # Handle admin buttons
    if data.startswith('admin_'):
        if user.id not in post_manager.authorized_users:
            await query.message.reply_text("❌ Anda tidak diizinkan.")
            return
        
        if data == 'admin_list':
            # Tampilkan list jadwal via callback
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
            # Mulai tambah jadwal
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
            # Kembali ke menu admin
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
    
    # Handle edit field buttons
    elif data.startswith('edit_field_'):
        parts = data.split('_')
        field = parts[2]  # time, text, image, active
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
            
            # Reschedule
            await schedule_next_run(context)
    
    # Handle regular buttons
    elif data == "login":
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
        # Tampilkan promo
        await send_promo(query.message, context)
        await query.delete_message()
    
    elif data == "menu_utama":
        # Kembali ke menu utama
        await start_command(update, context)

# ==================== FUNGSI KIRIM PROMO ====================

async def send_promo(message, context):
    """Kirim promo dengan gambar"""
    try:
        # Buat button untuk link
        keyboard = [
            [InlineKeyboardButton("🤖 BOT OFFICIAL", url="https://t.me/bolapelangi2_bot")],
            [InlineKeyboardButton("📈 PREDIKSI JITU", url="https://bopel2.vip/ChannelWA-Jadwal-Prediksi")],
            [InlineKeyboardButton("📢 CHANNEL WA", url="https://bopel2.vip/Channel-Whatsapp")],
            [InlineKeyboardButton("📢 CHANNEL TG", url="https://bopel2.vip/Channel-Telegram")],
            [InlineKeyboardButton("🟢 KLAIM BONUS", url="https://bopel2.link/wa")],
            [InlineKeyboardButton("🔙 KEMBALI KE MENU", callback_data="menu_utama")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Coba kirim dengan gambar
        try:
            # Coba ambil gambar dari jadwal pertama jika ada
            image_url = None
            for post in post_manager.posts.values():
                if post.get('image_url'):
                    image_url = post['image_url']
                    break
            
            if not image_url:
                image_url = "https://i.ibb.co/your-image/promo-banner.jpg"  # Default
            
            await message.reply_photo(
                photo=image_url,
                caption=PROMO_TEXT,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            logger.info("✅ Promo dengan gambar terkirim")
        except Exception as e:
            logger.warning(f"⚠️ Gagal kirim gambar: {e}, kirim teks saja")
            # Fallback: kirim teks saja
            await message.reply_text(
                text=PROMO_TEXT,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
                reply_markup=reply_markup
            )
    except Exception as e:
        logger.error(f"❌ Gagal kirim promo: {e}")

# ==================== COMMAND HANDLERS ====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command dengan BUTTON"""
    
    if update.callback_query:
        user = update.callback_query.from_user
        send = update.callback_query.edit_message_text
        logger.info(f"🚀 /start (via button) dari {user.first_name}")
    else:
        user = update.effective_user
        send = update.message.reply_text
        logger.info(f"🚀 /start dari {user.first_name} (ID: {user.id})")
    
    text = (
        f"Halo *{user.first_name}*! 👋\n\n"
        f"Selamat datang di *BOLAPELANGI 2 Bot*!\n\n"
        f"🤖 *Menu Utama:*\n"
        f"• Gunakan button di bawah untuk akses cepat\n"
        f"• Klik button LIHAT PROMO untuk promo terbaru\n"
        f"• Ketik /help untuk bantuan\n\n"
        f"🔥 *GasPoll!* 🔥"
    )
    
    # Button 3 sesuai permintaan + 1 button promo
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
    
    # Tambah button admin jika user terauthorisasi
    if user.id in post_manager.authorized_users:
        keyboard.append([InlineKeyboardButton("⚙️ ADMIN PANEL", callback_data='admin_back')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await send(
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=False,
            reply_markup=reply_markup
        )
        if not update.callback_query:
            logger.info(f"✅ Menu utama terkirim ke {user.first_name}")
    except Exception as e:
        logger.error(f"❌ Gagal kirim pesan: {e}")

async def promo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /promo command - Tampilkan promo dengan gambar"""
    user = update.effective_user
    logger.info(f"🎁 /promo dari {user.first_name}")
    await send_promo(update.message, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    user = update.effective_user
    logger.info(f"📚 /help dari {user.first_name}")
    
    text = (
        "📚 *BANTUAN BOT*\n\n"
        "✨ *Perintah Tersedia:*\n"
        "• /start - Tampilkan menu utama\n"
        "• /promo - Lihat promo terbaru\n"
        "• /help - Tampilkan bantuan ini\n\n"
    )
    
    # Tambah perintah admin jika user terauthorisasi
    if user.id in post_manager.authorized_users:
        text += (
            "\n👑 *Perintah Admin:*\n"
            "• /admin - Panel admin auto post\n"
            "• /list_jadwal - Lihat semua jadwal\n"
            "• /tambah_jadwal - Tambah jadwal baru\n"
            "• /edit_jadwal [id] - Edit jadwal\n"
            "• /hapus_jadwal [id] - Hapus jadwal\n"
            "• /aktifkan_jadwal [id] - Aktifkan jadwal\n"
            "• /nonaktifkan_jadwal [id] - Nonaktifkan jadwal\n"
        )
    
    text += "\n💬 *Butuh Bantuan?*\nHubungi WA Official:\n[🟢 KLIK DI SINI](https://bopel2.link/wa)\n\n⚽ *GasPoll!*"
    
    keyboard = [
        [InlineKeyboardButton("📞 HUBUNGI WA OFFICIAL", url='https://bopel2.link/wa')],
        [InlineKeyboardButton("🔙 KEMBALI KE MENU", callback_data='menu_utama')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        text=text, 
        parse_mode=ParseMode.MARKDOWN, 
        disable_web_page_preview=True,
        reply_markup=reply_markup
    )

# ==================== WELCOME NEW MEMBER ====================

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Fungsi untuk menyapa member baru yang bergabung ke channel
    """
    # Cek apakah ini pesan dari channel
    if not update.channel_post:
        return
    
    message = update.channel_post
    chat = update.effective_chat
    
    # Cek apakah ini channel target
    if chat.id != CHANNEL_ID:
        return
    
    # Cek apakah ada member baru
    if not message.new_chat_members:
        return
    
    logger.info(f"🎉 MEMBER BARU DETEKSI DI CHANNEL!")
    
    # Loop untuk setiap member baru
    for new_member in message.new_chat_members:
        # Jangan sapa bot sendiri
        if new_member.is_bot:
            continue
        
        # Dapatkan informasi member
        user_id = new_member.id
        first_name = new_member.first_name or "Member"
        
        logger.info(f"👤 Member baru: {first_name} (ID: {user_id})")
        
        # Buat mention
        mention = f"[{first_name}](tg://user?id={user_id})"
        
        # ===== KIRIM WELCOME DI CHANNEL =====
        welcome_text = (
            f"🎉 *SELAMAT DATANG* 🎉\n\n"
            f"Halo {mention}!\n"
            f"Selamat bergabung di *BOLAPELANGI 2 Official Channel*!\n\n"
            f"📌 *Link Penting:*\n"
            f"• [🤖 BOT OFFICIAL](https://t.me/bolapelangi2_bot)\n"
            f"• [🟢 WA KLAIM BONUS](https://bopel2.link/wa)\n"
            f"• [📢 CHANNEL WA](https://bopel2.vip/Channel-Whatsapp)\n"
            f"• [📢 CHANNEL TG](https://bopel2.vip/Channel-Telegram)\n\n"
            f"🔥 *GasPoll!* 🔥"
        )
        
        try:
            await context.bot.send_message(
                chat_id=chat.id,
                text=welcome_text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
            logger.info(f"✅ Welcome terkirim ke channel untuk {first_name}")
        except Exception as e:
            logger.error(f"❌ Gagal kirim welcome: {e}")

# ==================== TEST CHANNEL ====================

async def test_channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command untuk test kirim pesan ke channel"""
    user = update.effective_user
    logger.info(f"🧪 /test_channel dari {user.first_name}")
    
    try:
        test_message = await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text="🧪 *TEST BOT*\n\nBot aktif dan bisa mengirim pesan ke channel!",
            parse_mode=ParseMode.MARKDOWN
        )
        await update.message.reply_text(f"✅ Pesan test terkirim ke channel! (Message ID: {test_message.message_id})")
    except Exception as e:
        await update.message.reply_text(f"❌ Gagal kirim test: {e}")
        logger.error(f"❌ Gagal test kirim ke channel: {e}")

# ==================== ERROR HANDLER ====================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"❌ ERROR: {context.error}")

# ==================== POST INIT ====================

async def post_init(application: Application):
    """Fungsi yang dijalankan setelah bot initialized"""
    logger.info("=" * 50)
    logger.info("🤖 BOT BOLAPELANGI 2 DENGAN AUTO POST READY!")
    logger.info("=" * 50)
    
    try:
        bot_info = await application.bot.get_me()
        logger.info(f"✅ Bot: @{bot_info.username}")
        logger.info(f"✅ Channel ID: {CHANNEL_ID}")
        logger.info(f"✅ Total jadwal: {len(post_manager.posts)}")
        
        # Jadwalkan pengecekan pertama
        await schedule_next_run(application)
        
        # Kirim pesan startup ke channel
        try:
            await application.bot.send_message(
                chat_id=CHANNEL_ID,
                text="🤖 *Bot Auto Post Aktif*\n\n✅ Bot sudah online dan siap mengirim postingan terjadwal!",
                parse_mode=ParseMode.MARKDOWN
            )
            logger.info("✅ Pesan startup terkirim ke channel")
        except Exception as e:
            logger.error(f"❌ Tidak bisa kirim pesan startup ke channel: {e}")
            logger.error("   PASTIKAN BOT SUDAH JADI ADMIN CHANNEL!")
        
        logger.info("✅ Semua fitur siap digunakan!")
    except Exception as e:
        logger.error(f"❌ Gagal: {e}")

# ==================== MAIN FUNCTION ====================

def main():
    """Main function to run the bot"""
    
    print("=" * 60)
    print("🤖 BOT BOLAPELANGI 2 - DENGAN AUTO POST SCHEDULER")
    print("=" * 60)
    
    # Validasi token
    if not BOT_TOKEN or len(BOT_TOKEN) < 40:
        print("❌ ERROR: BOT_TOKEN tidak valid!")
        sys.exit(1)
    
    # Buat aplikasi
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
    application.add_handler(CommandHandler("promo", promo_command))
    application.add_handler(CommandHandler("test_channel", test_channel_command))
    
    # Admin commands
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("list_jadwal", list_jadwal_command))
    application.add_handler(CommandHandler("tambah_jadwal", tambah_jadwal_command))
    application.add_handler(CommandHandler("edit_jadwal", edit_jadwal_command))
    application.add_handler(CommandHandler("hapus_jadwal", hapus_jadwal_command))
    application.add_handler(CommandHandler("aktifkan_jadwal", aktifkan_jadwal_command))
    application.add_handler(CommandHandler("nonaktifkan_jadwal", nonaktifkan_jadwal_command))
    
    # Message handler untuk input
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input))
    
    # Callback handler untuk button
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
    
    print("=" * 60)
    print("📢 BOT RUNNING di RAILWAY")
    print("📢 Fitur: Auto Welcome | Auto Post Terjadwal | Promo dengan Gambar")
    print("📢 Button: LOGIN | DAFTAR | CLAIM EVENT | LIHAT PROMO")
    print("📢 Admin: /admin untuk panel auto post")
    print("📢 Jadwal Default: 08:00, 12:00, 19:00")
    print("=" * 60)
    sys.stdout.flush()
    
    # Jalankan bot
    application.run_polling(
        allowed_updates=["message", "channel_post", "callback_query"],
        drop_pending_updates=True
    )

if __name__ == "__main__":
    main()
