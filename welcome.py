"""
TELEGRAM WELCOME BOT - BOLAPELANGI 2
VERSI: WEBHOOK UNTUK RAILWAY
"""

import os
import logging
import sys
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# ==================== KONFIGURASI ====================

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8793227199:AAEXajy3RDO7SpMSCloj13Z4ubX3DXNvN4M")
CHANNEL_USERNAME = os.environ.get("CHANNEL_USERNAME", "@bolapelangi2_channel")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1003573191693"))
PORT = int(os.environ.get("PORT", 8080))
RAILWAY_PUBLIC_URL = os.environ.get("RAILWAY_PUBLIC_URL", "")

# ==================== KONFIGURASI LOGGING ====================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ==================== INIT BOT ====================

# Buat aplikasi Telegram
application = Application.builder().token(BOT_TOKEN).build()

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
    """Sapa member baru di channel"""
    if not update.channel_post:
        return
    
    message = update.channel_post
    chat = update.effective_chat
    
    if chat.id != CHANNEL_ID:
        return
    
    if not message.new_chat_members:
        return
    
    logger.info(f"🎉 New member detected in channel!")
    
    for new_member in message.new_chat_members:
        if new_member.is_bot:
            continue
        
        user_id = new_member.id
        first_name = new_member.first_name or "Member"
        
        mention = f"[{first_name}](tg://user?id={user_id})"
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
            logger.info(f"✅ Welcome sent to {first_name}")
        except Exception as e:
            logger.error(f"❌ Failed: {e}")
        
        try:
            private_text = (
                f"Halo {first_name}!\n\n"
                f"Terima kasih sudah bergabung dengan *BOLAPELANGI 2*! 🎉\n\n"
                f"⚽ *CASHBACK 100% MIX PARLAY*\n"
                f"• Modal Rp 10.000\n"
                f"• 5 tim TODAY\n"
                f"• Odds 1.80\n"
                f"• Max bonus Rp 300.000\n\n"
                f"📱 *Link:*\n"
                f"Klaim: https://bopel2.link/wa\n"
                f"Prediksi: https://bopel2.vip/ChannelWA-Jadwal-Prediksi\n\n"
                f"🚀 GasPoll!"
            )
            await context.bot.send_message(
                chat_id=user_id,
                text=private_text,
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.info(f"⚠️ Cannot send private: {e}")

# ==================== FLASK APP UNTUK WEBHOOK ====================

# Register handlers
application.add_handler(CommandHandler("start", start_command))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("promo", promo_command))
application.add_handler(CommandHandler("aturan", aturan_command))
application.add_handler(CommandHandler("kontak", kontak_command))
application.add_handler(
    MessageHandler(
        filters.Chat(chat_id=CHANNEL_ID) & filters.StatusUpdate.NEW_CHAT_MEMBERS,
        welcome_new_member
    )
)

# Flask app
app = Flask(__name__)

@app.route("/")
def index():
    return "Bot is running!", 200

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
async def webhook():
    """Handle Telegram webhook"""
    json_data = request.get_json(force=True)
    update = Update.de_json(json_data, application.bot)
    await application.process_update(update)
    return "OK", 200

@app.route("/setwebhook", methods=["GET"])
def set_webhook():
    """Set webhook URL"""
    if not RAILWAY_PUBLIC_URL:
        return "RAILWAY_PUBLIC_URL not set", 500
    
    webhook_url = f"{RAILWAY_PUBLIC_URL}/{BOT_TOKEN}"
    success = application.bot.set_webhook(url=webhook_url)
    if success:
        return f"Webhook set to {webhook_url}", 200
    return "Failed to set webhook", 500

# ==================== MAIN ====================

if __name__ == "__main__":
    print("=" * 60)
    print("🤖 BOT BOLAPELANGI 2 - WEBHOOK MODE")
    print("=" * 60)
    print(f"✅ Token: {BOT_TOKEN[:10]}...{BOT_TOKEN[-5:]}")
    print(f"✅ Channel: {CHANNEL_USERNAME}")
    print(f"✅ Port: {PORT}")
    print("=" * 60)
    
    # Hapus webhook lama kalau ada
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    bot = application.bot
    loop.run_until_complete(bot.delete_webhook())
    
    # Set webhook
    if RAILWAY_PUBLIC_URL:
        webhook_url = f"{RAILWAY_PUBLIC_URL}/{BOT_TOKEN}"
        loop.run_until_complete(bot.set_webhook(url=webhook_url))
        print(f"✅ Webhook set to: {webhook_url}")
    else:
        print("⚠️ RAILWAY_PUBLIC_URL not set. Set manually later.")
        print("   Go to: /setwebhook")
    
    print("=" * 60)
    print("📢 Running Flask server...")
    print("=" * 60)
    
    # Run Flask
    from waitress import serve
    serve(app, host="0.0.0.0", port=PORT)
