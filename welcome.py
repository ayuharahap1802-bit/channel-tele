"""
TELEGRAM WELCOME BOT - BOLAPELANGI 2
VERSI: DENGAN BUTTON INTERAKTIF
Fitur: Auto welcome + Button di /start
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

# ==================== BUTTON HANDLERS ====================

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    data = query.data
    
    logger.info(f"🔘 Button {data} diklik oleh {user.first_name}")
    
    if data == "login":
        text = "🔐 *Link Login*\n\nKlik link di bawah untuk login:\n[🔐 LOGIN SEKARANG](https://shortq.info/bolapelangi2)"
        await query.edit_message_text(text=text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=False)
    
    elif data == "daftar":
        text = "📝 *Link Daftar*\n\nKlik link di bawah untuk mendaftar:\n[📝 DAFTAR SEKARANG](https://rumahbopel2.com/_View/Register.aspx)"
        await query.edit_message_text(text=text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=False)
    
    elif data == "claim":
        text = "🎁 *Claim Event Parlay*\n\nKlik link di bawah untuk klaim bonus:\n[🎁 CLAIM BONUS](https://t.me/bolapelangi2_bot)"
        await query.edit_message_text(text=text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=False)
    
    elif data == "back":
        await start_command(update, context)

# ==================== COMMAND HANDLERS ====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command dengan BUTTON"""
    
    # Cek apakah ini callback query atau pesan biasa
    if update.callback_query:
        user = update.callback_query.from_user
        message = update.callback_query.message
        send = update.callback_query.edit_message_text
        logger.info(f"🚀 /start (via button) dari {user.first_name}")
    else:
        user = update.effective_user
        message = update.message
        send = update.message.reply_text
        logger.info(f"🚀 /start dari {user.first_name} (ID: {user.id})")
    
    # Teks utama
    text = (
        f"Halo {user.first_name}! 👋\n\n"
        f"Selamat datang di *BOLAPELANGI 2 Bot*!\n\n"
        f"🤖 *Apa yang bisa saya bantu?*\n"
        f"• Info promo terbaru\n"
        f"• Cara klaim bonus\n\n"
        f"📌 *Link Penting:*\n"
        f"• [🔥 KLAIM BONUS VIA WA](https://bopel2.link/wa)\n"
        f"• [📊 PREDIKSI & JADWAL](https://bopel2.vip/ChannelWA-Jadwal-Prediksi)\n\n"
        f"🔥 *GasPoll!* 🔥"
    )
    
    # Membuat button
    keyboard = [
        [
            InlineKeyboardButton("🔐 LOGIN", callback_data='login'),
            InlineKeyboardButton("📝 DAFTAR", callback_data='daftar'),
        ],
        [
            InlineKeyboardButton("🎁 CLAIM EVENT PARLAY", callback_data='claim'),
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Kirim pesan dengan button
    try:
        await send(
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=False,
            reply_markup=reply_markup
        )
        if not update.callback_query:
            logger.info(f"✅ Pesan dengan button terkirim ke {user.first_name}")
    except Exception as e:
        logger.error(f"❌ Gagal kirim pesan: {e}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    user = update.effective_user
    logger.info(f"📚 /help dari {user.first_name}")
    
    text = (
        "📚 *BANTUAN BOT BOLAPELANGI 2*\n\n"
        "*Fitur Bot:*\n"
        "• /start - Mulai bot & lihat menu\n"
        "• /help - Bantuan ini\n"
        "• /promo - Info promo terbaru\n"
        "• /aturan - Syarat & ketentuan\n"
        "• /kontak - Kontak official\n\n"
        "*Untuk Admin:*\n"
        "Bot akan otomatis menyapa member baru yang join ke channel\n\n"
        "*Kendala Teknis?*\n"
        "[💬 Hubungi WA Official](https://bopel2.link/wa)"
    )
    
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

async def promo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /promo command"""
    user = update.effective_user
    logger.info(f"🎁 /promo dari {user.first_name}")
    
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
        "• [🟢 KLAIM VIA WA](https://bopel2.link/wa)\n\n"
        "🚀 *GasPoll!*"
    )
    
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

async def aturan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /aturan command"""
    user = update.effective_user
    logger.info(f"📋 /aturan dari {user.first_name}")
    
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
        "• [📱 KIRIM BUKTI KE WA](https://bopel2.link/wa)"
    )
    
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

async def kontak_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /kontak command"""
    user = update.effective_user
    logger.info(f"📞 /kontak dari {user.first_name}")
    
    text = (
        "📞 *KONTAK OFFICIAL BOLAPELANGI 2*\n\n"
        "🟢 *WA Official (Klaim Bonus):*\n"
        "[👉 KLIK DISINI](https://bopel2.link/wa)\n\n"
        "📢 *Channel WhatsApp:*\n"
        "[👉 JOIN VIA LINK](https://bopel2.vip/Channel-Whatsapp)\n\n"
        "📢 *Channel Telegram:*\n"
        "[👉 JOIN VIA LINK](https://bopel2.vip/Channel-Telegram)\n\n"
        "🤖 *Bot Telegram:*\n"
        "@bolapelangi2_bot\n\n"
        "📈 *Prediksi & Jadwal:*\n"
        "[👉 CEK DI SINI](https://bopel2.vip/ChannelWA-Jadwal-Prediksi)\n\n"
        "🔥 *Follow semua biar gak ketinggalan info!*"
    )
    
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

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
            f"📌 *Link Penting (Klik Langsung):*\n"
            f"• [🤖 BOT OFFICIAL](https://t.me/bolapelangi2_bot)\n"
            f"• [🟢 WA KLAIM BONUS](https://bopel2.link/wa)\n"
            f"• [📢 CHANNEL WA](https://bopel2.vip/Channel-Whatsapp)\n"
            f"• [📢 CHANNEL TG](https://bopel2.vip/Channel-Telegram)\n"
            f"• [📊 PREDIKSI JITU](https://bopel2.vip/ChannelWA-Jadwal-Prediksi)\n\n"
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
        
        # ===== KIRIM PESAN PRIVATE KE MEMBER =====
        try:
            private_text = (
                f"Halo {first_name}! 👋\n\n"
                f"Terima kasih sudah bergabung dengan *BOLAPELANGI 2*! 🎉\n\n"
                f"⚽ *PROMO SPESIAL UNTUK MEMBER BARU*\n"
                f"• *CASHBACK 100% MIX PARLAY*\n"
                f"• Modal Rp 10.000\n"
                f"• 5 tim TODAY\n"
                f"• Odds 1.80\n"
                f"• Max bonus Rp 300.000/hari\n\n"
                f"📱 *Link Penting (Klik Langsung):*\n"
                f"• [🔥 KLAIM BONUS VIA WA](https://bopel2.link/wa)\n"
                f"• [📊 PREDIKSI JITU](https://bopel2.vip/ChannelWA-Jadwal-Prediksi)\n"
                f"• [📢 CHANNEL WHATSAPP](https://bopel2.vip/Channel-Whatsapp)\n"
                f"• [📢 CHANNEL TELEGRAM](https://bopel2.vip/Channel-Telegram)\n\n"
                f"Jangan lupa follow semua channel official ya Bosku!\n\n"
                f"🚀 *GasPoll terus!*"
            )
            
            await context.bot.send_message(
                chat_id=user_id,
                text=private_text,
                parse_mode=ParseMode.MARKDOWN
            )
            logger.info(f"✅ Private message terkirim ke {first_name}")
        except Exception as e:
            logger.info(f"⚠️ Tidak bisa kirim private ke {first_name}: {e}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"❌ ERROR: {context.error}")

async def post_init(application: Application):
    """Fungsi yang dijalankan setelah bot initialized"""
    logger.info("=" * 50)
    logger.info("🤖 BOT BOLAPELANGI 2 READY!")
    logger.info("=" * 50)
    
    # Cek koneksi
    try:
        bot_info = await application.bot.get_me()
        logger.info(f"✅ Bot: @{bot_info.username}")
        logger.info(f"✅ Channel ID: {CHANNEL_ID}")
        logger.info("✅ Button sudah terpasang di /start")
    except Exception as e:
        logger.error(f"❌ Gagal: {e}")

# ==================== MAIN FUNCTION ====================

def main():
    """Main function to run the bot"""
    
    print("=" * 60)
    print("🤖 BOT BOLAPELANGI 2 - DENGAN BUTTON")
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
    application.add_handler(CommandHandler("aturan", aturan_command))
    application.add_handler(CommandHandler("kontak", kontak_command))
    
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
    print("📢 Fitur Button: AKTIF")
    print("📢 Button: LOGIN | DAFTAR | CLAIM EVENT PARLAY")
    print("=" * 60)
    sys.stdout.flush()
    
    # Jalankan bot
    application.run_polling(
        allowed_updates=["message", "channel_post", "callback_query"],
        drop_pending_updates=True
    )

if __name__ == "__main__":
    main()
