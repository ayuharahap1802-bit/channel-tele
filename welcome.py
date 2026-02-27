"""
TELEGRAM WELCOME BOT - BOLAPELANGI 2
Script untuk menyapa member baru yang join ke channel
Created for: @bolapelangi2_bot
"""

import logging
from telegram import Update, ChatMember
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# ==================== KONFIGURASI ====================

# GANTI DENGAN TOKEN BOT KAMU!
BOT_TOKEN = "8793227199:AAEXajy3RDO7SpMSCloj13Z4ubX3DXNvN4M"

# GANTI DENGAN USERNAME CHANNEL KAMU!
CHANNEL_USERNAME = "@bolapelangi2_channel"  # ISI DENGAN USERNAME CHANNEL ASLI!

# ID CHANNEL (SUDAH BENAR)
CHANNEL_ID = -1003573191693

# ==================== KONFIGURASI LOGGING ====================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== FUNGSI UTAMA ====================

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
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

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
    # Cek apakah ini message dari channel
    if not update.channel_post:
        return
    
    message = update.channel_post
    chat = update.effective_chat
    
    # Log untuk debugging
    logger.info(f"Message received in chat {chat.id} ({chat.title})")
    
    # Cek apakah ini di channel yang kita targetkan
    if chat.id != CHANNEL_ID:
        logger.info(f"Ignoring chat {chat.id} - not target channel")
        return
    
    # Cek apakah ada member baru
    if not message.new_chat_members:
        return
    
    logger.info(f"🎉 New member detected in channel!")
    
    # Loop untuk setiap member baru
    for new_member in message.new_chat_members:
        # Jangan sapa bot sendiri
        if new_member.is_bot:
            logger.info(f"Ignoring bot: {new_member.first_name}")
            continue
        
        # Dapatkan informasi member
        user_id = new_member.id
        first_name = new_member.first_name or "Member"
        username = f"@{new_member.username}" if new_member.username else first_name
        
        logger.info(f"👤 New human member: {first_name} (ID: {user_id})")
        
        # Buat mention
        mention = f"[{first_name}](tg://user?id={user_id})"
        
        # Kirim pesan welcome ke channel
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
                chat_id=chat.id,
                text=welcome_text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
            logger.info(f"✅ Welcome message sent to {first_name} in channel")
        except Exception as e:
            logger.error(f"❌ Failed to send welcome message in channel: {e}")
        
        # Coba kirim pesan private
        try:
            private_text = (
                f"Halo {first_name}!\n\n"
                f"Terima kasih sudah bergabung dengan *BOLAPELANGI 2*! 🎉\n\n"
                f"Kami punya PROMO SPESIAL untuk member baru:\n"
                f"⚽ *CASHBACK 100% MIX PARLAY*\n"
                f"• Modal Rp 10.000\n"
                f"• 5 tim TODAY\n"
                f"• Odds 1.80\n"
                f"• Max bonus Rp 300.000\n\n"
                f"📱 *Link Penting:*\n"
                f"• Klaim Bonus: https://bopel2.link/wa\n"
                f"• Prediksi Jitu: https://bopel2.vip/ChannelWA-Jadwal-Prediksi\n\n"
                f"GasPoll terus Bosku! 🚀"
            )
            
            await context.bot.send_message(
                chat_id=user_id,
                text=private_text,
                parse_mode=ParseMode.MARKDOWN
            )
            logger.info(f"✅ Private message sent to {first_name}")
        except Exception as e:
            logger.info(f"⚠️ Could not send private message to {first_name}: {e}")
            # Ini normal jika user belum pernah chat dengan bot

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"❌ Update {update} caused error {context.error}")

# ==================== MAIN FUNCTION ====================

def main():
    """Main function to run the bot"""
    
    # Buat aplikasi
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Tambahkan command handlers (PAKAI COMMANDHANDLER, LEBIH SIMPEL)
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("promo", promo_command))
    application.add_handler(CommandHandler("aturan", aturan_command))
    application.add_handler(CommandHandler("kontak", kontak_command))
    
    # Handler untuk welcome message (via channel post)
    application.add_handler(
        MessageHandler(
            filters.Chat(chat_id=CHANNEL_ID) & filters.StatusUpdate.NEW_CHAT_MEMBERS,
            welcome_new_member
        )
    )
    
    # Error handler
    application.add_error_handler(error_handler)
    
    # Start bot
    print("=" * 50)
    print("🤖 BOT BOLAPELANGI 2 WELCOME BOT")
    print("=" * 50)
    print(f"✅ Token: {BOT_TOKEN[:10]}...{BOT_TOKEN[-5:]}")
    print(f"✅ Target Channel: {CHANNEL_USERNAME}")
    print(f"✅ Channel ID: {CHANNEL_ID}")
    print("=" * 50)
    print("📢 Status: RUNNING")
    print("📢 Menunggu member baru...")
    print("=" * 50)
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    # Run bot dengan polling
    application.run_polling(allowed_updates=["message", "channel_post", "chat_member"])

if __name__ == "__main__":
    main()
