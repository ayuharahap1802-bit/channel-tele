#!/usr/bin/env python3
"""
Telegram Bot with Advanced Features
Main entry point for Railway deployment
Version: 1.0.0
"""

import logging
import sys
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram.error import TelegramError

# Import configuration
from config import Config

# Import database
from database import init_settings, get_db

# Import handlers
from handlers.public import setup_public_handlers
from handlers.admin import setup_admin_handlers
from handlers.superadmin import setup_superadmin_handlers

# Import scheduler
from scheduler import BotScheduler

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        """Initialize the bot"""
        self.token = Config.BOT_TOKEN
        self.app = None
        self.scheduler = None
        
        # Validate token
        if not self.token:
            logger.error("❌ No BOT_TOKEN provided! Please set in environment variables.")
            sys.exit(1)
        
        # Initialize database settings
        try:
            init_settings()
            logger.info("✅ Database initialized successfully")
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            sys.exit(1)
    
    async def error_handler(self, update: Update, context):
        """Handle errors"""
        logger.error(f"Update {update} caused error {context.error}")
        
        try:
            if update and update.effective_message:
                await update.effective_message.reply_text(
                    "❌ An error occurred. Please try again later."
                )
        except:
            pass
    
    async def start_command(self, update: Update, context):
        """Start command handler"""
        await update.message.reply_text(
            "🤖 *Bot is running!*\n\n"
            "Use /help to see available commands.",
            parse_mode='Markdown'
        )
    
    async def help_command(self, update: Update, context):
        """Help command handler"""
        help_text = """
📋 *Available Commands:*

*Public Commands:*
/start - Start the bot
/help - Show this help
/info - Your account info
/stats - Bot statistics

*Admin Commands:*
/admin - Admin dashboard
/users - Manage users
/broadcast - Send broadcast

*Super Admin:*
/admins - Manage admins
/settings - View settings
/backup - Backup database
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def health_check(self, update: Update, context):
        """Health check endpoint"""
        enabled_features = [k for k, v in Config.FEATURES.items() if v]
        await update.message.reply_text(
            "✅ *Bot is healthy!*\n\n"
            f"• Status: Online\n"
            f"• Features: {len(enabled_features)} enabled\n"
            f"• Version: 1.0.0",
            parse_mode='Markdown'
        )
    
    async def cancel_command(self, update: Update, context):
        """Cancel current operation"""
        context.user_data.clear()
        await update.message.reply_text("✅ Operation cancelled.")
    
    def setup_handlers(self):
        """Setup all command handlers"""
        
        # Basic commands
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("health", self.health_check))
        self.app.add_handler(CommandHandler("cancel", self.cancel_command))
        
        # Public handlers
        setup_public_handlers(self.app)
        
        # Admin handlers
        setup_admin_handlers(self.app)
        
        # Super admin handlers
        setup_superadmin_handlers(self.app)
        
        # Error handler
        self.app.add_error_handler(self.error_handler)
        
        logger.info("✅ All handlers registered successfully")
    
    def run(self):
        """Run the bot"""
        try:
            # Create application
            self.app = Application.builder().token(self.token).build()
            
            # Setup handlers
            self.setup_handlers()
            
            # Setup scheduler
            self.scheduler = BotScheduler(self.app.bot)
            self.scheduler.start()
            
            # Start bot
            logger.info("🚀 Starting bot...")
            logger.info(f"🤖 Bot username: @{Config.BOT_USERNAME}")
            logger.info(f"👑 Super admins: {Config.SUPER_ADMIN_IDS}")
            
            self.app.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
            
        except TelegramError as e:
            logger.error(f"❌ Telegram error: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            sys.exit(1)
        finally:
            if self.scheduler:
                self.scheduler.stop()

def main():
    """Main entry point"""
    print("=" * 60)
    print("🚀 Starting Telegram Bot with Advanced Features")
    print("=" * 60)
    
    # Run bot
    bot = TelegramBot()
    bot.run()

if __name__ == "__main__":
    main()
