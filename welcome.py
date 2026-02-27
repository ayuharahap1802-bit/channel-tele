"""
TELEGRAM WELCOME BOT - BOLAPELANGI 2
VERSI: POLLING UNTUK TERMINAL/LOKAL
Fitur: Auto welcome saat ada member baru join channel
Created for: @bolapelangi2_bot
"""

import os
import logging
import sys
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# ==================== KONFIGURASI ====================

# Token bot dari BotFather
BOT_TOKEN = "8793227199:AAEXajy3RDO7SpMSCloj13Z4ubX3DXNvN4M"

# Username channel (ganti dengan username channel Anda)
CHANNEL_USERNAME = "@bolapelangi2_channel"

# ID Channel (dapatkan dengan bot @getidsbot)
CHANNEL_ID = -1003573191693

# ==================== KONFIGURASI LOGGING ====================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ==================== COMMAND HANDLERS ====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    text = (
        f"Halo {user.first_name}! 👋\n\n"
        f"Selamat datang di *BOLAPELANGI 2 Bot*!\n\n"
        f"🤖 *Apa yang bisa saya bantu?*\n"
        f"• Saya akan menyapa member baru di channel\n"
        f"• Info promo terbaru\n"
        f"• Cara klaim bonus\n\n"
        f"📌 *Link Penting:*\n"
        f"• Channel: {CHANNEL_USERNAME}\n"
        f"• Klaim Bonus: https://bopel2.link/wa\n"
        f"• Prediksi: https://bopel2.vip/ChannelWA-Jadwal-Prediksi\n\n"
        f"🔥 *GasPoll!* 🔥"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    text = (
        "📚 *BANTUAN BOT BOLAPELANGI 2*\n\n"
        "*Fitur Bot:*\n"
        "• /start - Mulai bot\n"
        "• /help - Bantuan ini\n"
        "• /promo - Info promo terbaru\n"
        "• /aturan - Syarat & ketentuan\n"
        "• /kontak - Kontak official\n\n"
        "*Untuk Admin:*\n"
        f"Bot akan otomatis menyapa member baru yang join ke channel {CHANNEL_USERNAME}\n\n"
        "*Kendala Teknis?*\n"
        "Hubungi WA Official: https://bopel2.link/wa"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

async def promo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /promo command"""
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
    """
    Fungsi untuk menyapa member baru yang bergabung ke channel
    """
    # Cek apakah ini pesan dari channel
    if not update.channel_post:
        return
    
    message = update.channel_post
    chat = update.effective_chat
    
    # Log untuk debugging
    logger.info(f"📨 Pesan diterima dari chat {chat.id} ({chat.title})")
    
    # Cek apakah ini channel target
    if chat.id != CHANNEL_ID:
        logger.info(f"⏭️ Bukan channel target ({chat.id} != {CHANNEL_ID})")
        return
    
    # Cek apakah ada member baru
    if not message.new_chat_members:
        logger.info("ℹ️ Tidak ada member baru dalam pesan ini")
        return
    
    logger.info(f"🎉 MEMBER BARU DETEKSI DI CHANNEL!")
    
    # Loop untuk setiap member baru
    for new_member in message.new_chat_members:
        # Jangan sapa bot sendiri
        if new_member.is_bot:
            logger.info(f"🤖 Mengabaikan bot: {new_member.first_name}")
            continue
        
        # Dapatkan informasi member
        user_id = new_member.id
        first_name = new_member.first_name or "Member"
        username = f"@{new_member.username}" if new_member.username else first_name
        
        logger.info(f"👤 Member baru: {first_name} (ID: {user_id})")
        
        # Buat mention (format untuk Markdown)
        mention = f"[{first_name}](tg://user?id={user_id})"
        
        # ===== KIRIM WELCOME DI CHANNEL =====
        welcome_text = (
            f"🎉 *SELAMAT DATANG* 🎉\n\n"
            f"Halo {mention}!\n"
            f"Selamat bergabung di *BOLAPELANGI 2 Official Channel*!\n\n"
            f"Jangan lupa follow:\n"
            f"• Bot: @bolapelangi2_bot\n"
            f"• WA: [Klik Disini](https://bopel2.vip/Channel-Whatsapp)\n"
            f"• TG: [Klik Disini](https://bopel2.vip/Channel-Telegram)\n\n"
            f"🔥 *GasPoll!* 🔥"
        )
        
        try:
            await context.bot.send_message(
                chat_id=chat.id,  # Kirim ke channel
                text=welcome_text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
            logger.info(f"✅ Pesan welcome terkirim ke channel untuk {first_name}")
        except Exception as e:
            logger.error(f"❌ Gagal kirim pesan ke channel: {e}")
        
        # ===== KIRIM PESAN PRIVATE KE MEMBER =====
        try:
            private_text = (
                f"Halo {first_name}! 👋\n\n"
                f"Terima kasih sudah bergabung dengan *BOLAPELANGI 2*! 🎉\n\n"
                f"Kami punya *PROMO SPESIAL* untuk member baru:\n"
                f"⚽ *CASHBACK 100% MIX PARLAY*\n"
                f"• Modal Rp 10.000\n"
                f"• 5 tim TODAY\n"
                f"• Odds 1.80\n"
                f"• Max bonus Rp 300.000/hari\n\n"
                f"📱 *Link Penting:*\n"
                f"• Klaim Bonus: https://bopel2.link/wa\n"
                f"• Prediksi Jitu: https://bopel2.vip/ChannelWA-Jadwal-Prediksi\n\n"
                f"GasPoll terus Bosku! 🚀"
            )
            
            await context.bot.send_message(
                chat_id=user_id,  # Kirim ke personal chat
                text=private_text,
                parse_mode=ParseMode.MARKDOWN
            )
            logger.info(f"✅ Pesan private terkirim ke {first_name}")
        except Exception as e:
            logger.info(f"⚠️ Tidak bisa kirim pesan private ke {first_name}: {e}")
            # Ini normal jika user belum pernah chat dengan bot

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"❌ ERROR: Update {update} caused error {context.error}")

# ==================== MAIN FUNCTION ====================

def main():
    """Main function to run the bot"""
    
    # Buat aplikasi
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Tambahkan command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("promo", promo_command))
    application.add_handler(CommandHandler("aturan", aturan_command))
    application.add_handler(CommandHandler("kontak", kontak_command))
    
    # Handler untuk welcome message (via channel post)
    # Filter khusus: hanya dari channel ID tertentu dan event new chat members
    application.add_handler(
        MessageHandler(
            filters.Chat(chat_id=CHANNEL_ID) & filters.StatusUpdate.NEW_CHAT_MEMBERS,
            welcome_new_member
        )
    )
    
    # Error handler
    application.add_error_handler(error_handler)
    
    # Tampilkan informasi bot
    print("=" * 60)
    print("🤖 BOT BOLAPELANGI 2 WELCOME BOT")
    print("=" * 60)
    print(f"✅ Token: {BOT_TOKEN[:10]}...{BOT_TOKEN[-5:]}")
    print(f"✅ Channel Target: {CHANNEL_USERNAME}")
    print(f"✅ Channel ID: {CHANNEL_ID}")
    print("=" * 60)
    print("📢 Status: RUNNING (POLLING MODE)")
    print("📢 Bot siap menyapa member baru di channel")
    print("📢 Tekan Ctrl+C untuk menghentikan bot")
    print("=" * 60)
    
    # Jalankan bot dengan polling
    application.run_polling(allowed_updates=["message", "channel_post"])

if __name__ == "__main__":
    main()
