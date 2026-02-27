"""
TELEGRAM WELCOME BOT - BOLAPELANGI 2
VERSI: DEBUG - UNTUK CEK KENAPA BOT TIDAK RESPON
"""

import os
import logging
import sys
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# ==================== KONFIGURASI DARI ENVIRONMENT ====================

print("=" * 60)
print("🔍 DEBUG MODE: MEMULAI BOT...")
print("=" * 60)

# Baca dari environment variable Railway
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID_STR = os.environ.get("CHANNEL_ID")

print(f"🔍 BOT_TOKEN dari env: {'ADA' if BOT_TOKEN else 'TIDAK ADA'}")
print(f"🔍 CHANNEL_ID dari env: {CHANNEL_ID_STR}")

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
    level=logging.DEBUG,  # UBAH KE DEBUG UNTUK LIHAT SEMUA
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ==================== COMMAND HANDLERS ====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    logger.info("=" * 40)
    logger.info("🚀 START COMMAND DIPANGGIL!")
    logger.info("=" * 40)
    
    # Debug info
    user = update.effective_user
    chat = update.effective_chat
    
    logger.info(f"User ID: {user.id}")
    logger.info(f"User First Name: {user.first_name}")
    logger.info(f"User Username: {user.username}")
    logger.info(f"Chat ID: {chat.id}")
    logger.info(f"Chat Type: {chat.type}")
    
    # Coba kirim pesan sederhana dulu
    try:
        sent_message = await update.message.reply_text("✅ Bot merespon!")
        logger.info(f"Pesan terkirim: {sent_message.message_id}")
    except Exception as e:
        logger.error(f"GAGAL KIRIM PESAN: {e}")
        return
    
    # Kirim pesan lengkap
    text = (
        f"Halo {user.first_name}! 👋\n\n"
        f"Selamat datang di *BOLAPELANGI 2 Bot*!\n\n"
        f"🤖 *Apa yang bisa saya bantu?*\n"
        f"• Saya akan menyapa member baru di channel\n"
        f"• Info promo terbaru\n"
        f"• Cara klaim bonus\n\n"
        f"📌 *Link Penting:*\n"
        f"• Klaim Bonus: https://bopel2.link/wa\n"
        f"• Prediksi: https://bopel2.vip/ChannelWA-Jadwal-Prediksi\n\n"
        f"🔥 *GasPoll!* 🔥"
    )
    
    try:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
        logger.info("✅ Pesan lengkap terkirim")
    except Exception as e:
        logger.error(f"❌ Gagal kirim pesan lengkap: {e}")
        # Coba kirim tanpa markdown
        try:
            await update.message.reply_text(text.replace("*", ""))
            logger.info("✅ Pesan tanpa markdown terkirim")
        except Exception as e2:
            logger.error(f"❌ Gagal total: {e2}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    logger.info("📚 HELP COMMAND dipanggil")
    text = (
        "📚 *BANTUAN BOT BOLAPELANGI 2*\n\n"
        "*Fitur Bot:*\n"
        "• /start - Mulai bot\n"
        "• /help - Bantuan ini\n"
        "• /promo - Info promo terbaru\n"
        "• /aturan - Syarat & ketentuan\n"
        "• /kontak - Kontak official\n\n"
        "*Untuk Admin:*\n"
        "Bot akan otomatis menyapa member baru yang join ke channel\n\n"
        "*Kendala Teknis?*\n"
        "Hubungi WA Official: https://bopel2.link/wa"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

async def promo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /promo command"""
    logger.info("🎁 PROMO COMMAND dipanggil")
    text = (
        "🎁 *PROMO SPESIAL BOLAPELANGI 2* 🎁\n\n"
        "⚽ *CASHBACK 100% MIX PARLAY*\n"
        "• Minimal Bet: Rp 10.000\n"
        "• Minimal 5 tim (TODAY)\n"
        "• Odds Minimal 1.80\n"
        "• 1 tim Lose, sisanya Win Full\n"
        "• Max Bonus: Rp 300.000/hari\n\n"
        "📌 *Syarat:*\n"
        "• Follow semua channel official\n"
        "• Add Telegram Bot: @bolapelangi2_bot\n"
        "• Klaim via WA: https://bopel2.link/wa\n\n"
        "🚀 *GasPoll!*"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

async def aturan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /aturan command"""
    logger.info("📋 ATURAN COMMAND dipanggil")
    text = (
        "📋 *SYARAT & KETENTUAN*\n\n"
        "1. Bonus hanya bisa diklaim *1x sehari*\n"
        "2. Maksimal bonus *Rp 300.000/hari*\n"
        "3. Tidak boleh ada *kesamaan IP*\n"
        "4. Tidak boleh *safety bet* atau kecurangan\n"
        "5. Keputusan admin *mutlak*\n\n"
        "⚠️ Jika ketahuan curang, bonus *HANGUS*!\n\n"
        "✅ *Cara Klaim:*\n"
        "• Gabung semua channel official\n"
        "• Add bot @bolapelangi2_bot\n"
        "• Kirim bukti ke WA: https://bopel2.link/wa"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

async def kontak_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /kontak command"""
    logger.info("📞 KONTAK COMMAND dipanggil")
    text = (
        "📞 *KONTAK OFFICIAL BOLAPELANGI 2*\n\n"
        "🟢 *WA Official (Klaim Bonus):*\n"
        "https://bopel2.link/wa\n\n"
        "📢 *Channel WhatsApp:*\n"
        "https://bopel2.vip/Channel-Whatsapp\n\n"
        "📢 *Channel Telegram:*\n"
        "https://bopel2.vip/Channel-Telegram\n\n"
        "🤖 *Bot Telegram:*\n"
        "@bolapelangi2_bot\n\n"
        "📈 *Prediksi & Jadwal:*\n"
        "https://bopel2.vip/ChannelWA-Jadwal-Prediksi\n\n"
        "🔥 *Follow semua biar gak ketinggalan info!*"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sapa member baru di channel"""
    logger.info("👋 WELCOME FUNCTION DIPANGGIL")
    
    if not update.channel_post:
        logger.info("❌ Bukan channel post")
        return
    
    message = update.channel_post
    chat = update.effective_chat
    
    logger.info(f"📨 Dari chat: {chat.id} - {chat.title}")
    logger.info(f"📨 Channel ID target: {CHANNEL_ID}")
    
    if chat.id != CHANNEL_ID:
        logger.info(f"⏭️ Bukan channel target")
        return
    
    if not message.new_chat_members:
        logger.info("ℹ️ Tidak ada member baru")
        return
    
    logger.info(f"🎉 ADA {len(message.new_chat_members)} MEMBER BARU!")
    
    for new_member in message.new_chat_members:
        if new_member.is_bot:
            logger.info(f"🤖 Bot: {new_member.first_name}")
            continue
        
        logger.info(f"👤 Member: {new_member.first_name} (ID: {new_member.id})")
        
        # Sisanya sama seperti sebelumnya...

async def debug_all_updates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk debug semua update"""
    logger.info("=" * 50)
    logger.info("🔍 UPDATE DITERIMA:")
    logger.info(f"Update ID: {update.update_id}")
    
    if update.message:
        logger.info(f"Type: MESSAGE")
        logger.info(f"Text: {update.message.text}")
        logger.info(f"From: {update.message.from_user.first_name} (ID: {update.message.from_user.id})")
        logger.info(f"Chat: {update.message.chat.id} - {update.message.chat.type}")
    
    if update.channel_post:
        logger.info(f"Type: CHANNEL POST")
        logger.info(f"Chat: {update.channel_post.chat.id} - {update.channel_post.chat.title}")
    
    if update.my_chat_member:
        logger.info(f"Type: MY_CHAT_MEMBER")
    
    logger.info("=" * 50)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"❌ ERROR: {context.error}")
    if update:
        logger.error(f"Update: {update}")

async def post_init(application: Application):
    """Fungsi yang dijalankan setelah bot initialized"""
    logger.info("=" * 50)
    logger.info("🤖 BOT INITIALIZED - READY TO ROCK!")
    logger.info("=" * 50)
    
    # Cek koneksi ke Telegram
    try:
        bot_info = await application.bot.get_me()
        logger.info(f"✅ Bot Info: @{bot_info.username} (ID: {bot_info.id})")
        logger.info(f"✅ Bot bisa menerima pesan!")
    except Exception as e:
        logger.error(f"❌ Gagal get bot info: {e}")

# ==================== MAIN FUNCTION ====================

def main():
    """Main function to run the bot"""
    
    print("=" * 60)
    print("🚀 MEMULAI BOT DENGAN DEBUG MODE...")
    print("=" * 60)
    
    # Validasi token
    if not BOT_TOKEN:
        print("❌ ERROR: BOT_TOKEN tidak ada!")
        sys.exit(1)
    
    if len(BOT_TOKEN) < 40:
        print(f"❌ ERROR: BOT_TOKEN terlalu pendek: {BOT_TOKEN}")
        sys.exit(1)
    
    print(f"✅ BOT_TOKEN valid")
    
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
        print(f"❌ Gagal buat application: {e}")
        sys.exit(1)
    
    # TAMBAHKAN DEBUG HANDLER UNTUK MELIHAT SEMUA UPDATE
    application.add_handler(MessageHandler(filters.ALL, debug_all_updates), group=-1)
    
    # Command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("promo", promo_command))
    application.add_handler(CommandHandler("aturan", aturan_command))
    application.add_handler(CommandHandler("kontak", kontak_command))
    
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
    print("📢 BOT STARTED - WAITING FOR UPDATES...")
    print("📢 Kirim /start ke bot di Telegram")
    print("=" * 60)
    sys.stdout.flush()
    
    # Jalankan bot
    application.run_polling(
        allowed_updates=["message", "channel_post", "chat_member"],
        drop_pending_updates=True,
        timeout=30
    )

if __name__ == "__main__":
    main()
