"""
TELEGRAM WELCOME BOT - BOLAPELANGI 2
VERSI: FINAL UNTUK BOTFATHER
Fitur: Auto welcome + Promo dengan gambar
Created for: @bolapelangi2_bot
"""

import os
import logging
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode

# ==================== KONFIGURASI DARI ENVIRONMENT ====================

print("=" * 60)
print("🔍 MEMULAI BOT BOLAPELANGI 2...")
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
🤖 [BOT OFFICIAL](https://t.me/bolapelangi2_bot)
📈 [PREDIKSI JITU](https://bopel2.vip/ChannelWA-Jadwal-Prediksi)
📢 [CHANNEL WHATSAPP](https://bopel2.vip/Channel-Whatsapp)
📢 [CHANNEL TELEGRAM](https://bopel2.vip/Channel-Telegram)
🟢 [KLAIM BONUS](https://bopel2.link/wa)

📌 *Catatan:* 1x/hari, no IP sama, no safety bet
🚀 *GASPOLL TERUS BOSKU!*
"""

# ==================== PATH GAMBAR ====================
# Ganti dengan URL gambar Anda (upload ke imgbb.com atau postimages.org)
PROMO_IMAGE_URL = "https://i.ibb.co/your-image/promo-banner.jpg"  # GANTI DENGAN URL GAMBAR ANDA!

# ==================== BUTTON HANDLERS ====================

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    data = query.data
    
    logger.info(f"🔘 Button {data} diklik oleh {user.first_name}")
    
    if data == "login":
        # Kirim link login
        text = "🔐 *Link Login*\n\nKlik tombol di bawah untuk login:"
        keyboard = [[InlineKeyboardButton("🔐 LOGIN SEKARANG", url="https://bopel2.link/login")]]
        await query.message.reply_text(
            text=text, 
            parse_mode=ParseMode.MARKDOWN, 
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        await query.delete_message()
    
    elif data == "daftar":
        # Kirim link daftar
        text = "📝 *Link Daftar*\n\nKlik tombol di bawah untuk mendaftar:"
        keyboard = [[InlineKeyboardButton("📝 DAFTAR SEKARANG", url="https://bopel2.link/daftar")]]
        await query.message.reply_text(
            text=text, 
            parse_mode=ParseMode.MARKDOWN, 
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        await query.delete_message()
    
    elif data == "claim":
        # Kirim link claim
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
            await message.reply_photo(
                photo=PROMO_IMAGE_URL,
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
        "💬 *Butuh Bantuan?*\n"
        "Hubungi WA Official:\n"
        "[🟢 KLIK DI SINI](https://bopel2.link/wa)\n\n"
        "⚽ *GasPoll!*"
    )
    
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
    logger.info("🤖 BOT BOLAPELANGI 2 READY!")
    logger.info("=" * 50)
    
    try:
        bot_info = await application.bot.get_me()
        logger.info(f"✅ Bot: @{bot_info.username}")
        logger.info(f"✅ Channel ID: {CHANNEL_ID}")
        
        # Kirim pesan startup ke channel
        try:
            await application.bot.send_message(
                chat_id=CHANNEL_ID,
                text="🤖 *Bot Aktif*\n\nBot sudah online dan siap menyapa member baru!",
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
    print("🤖 BOT BOLAPELANGI 2 - FINAL VERSION")
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
    print("📢 Fitur: Auto Welcome | Promo dengan Gambar")
    print("📢 Button: LOGIN | DAFTAR | CLAIM EVENT | LIHAT PROMO")
    print("📢 Command: /start, /promo, /help, /test_channel")
    print("=" * 60)
    sys.stdout.flush()
    
    # Jalankan bot
    application.run_polling(
        allowed_updates=["message", "channel_post", "callback_query"],
        drop_pending_updates=True
    )

if __name__ == "__main__":
    main()
