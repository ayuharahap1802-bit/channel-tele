#!/usr/bin/env python3
"""
Telegram Bot with Advanced Features
Main entry point for Railway deployment
"""

import logging
import sys
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
from telegram.error import TelegramError

# Import configuration
from config import Config

# Import database
from database import init_settings, get_db

# Import handlers
from handlers import public, admin, superadmin

# Import scheduler
from scheduler import BotScheduler

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
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
            logger.error("No BOT_TOKEN provided! Please set in environment variables.")
            sys.exit(1)
        
        # Initialize database settings
        init_settings()
        logger.info("Database initialized")
    
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
    
    async def health_check(self, update: Update, context):
        """Health check endpoint"""
        await update.message.reply_text(
            "✅ Bot is healthy!\n\n"
            f"Uptime: Running\n"
            f"Features: {', '.join([k for k, v in Config.FEATURES.items() if v])}"
        )
    
    async def cancel_command(self, update: Update, context):
        """Cancel current operation"""
        context.user_data.clear()
        await update.message.reply_text("✅ Operation cancelled.")
    
    def setup_handlers(self):
        """Setup all command handlers"""
        
        # Public handlers
        public.setup_public_handlers(self.app)
        
        # Admin handlers
        admin.setup_admin_handlers(self.app)
        
        # Super admin handlers
        superadmin.setup_superadmin_handlers(self.app)
        
        # General handlers
        self.app.add_handler(CommandHandler("health", self.health_check))
        self.app.add_handler(CommandHandler("cancel", self.cancel_command))
        
        # Error handler
        self.app.add_error_handler(self.error_handler)
        
        logger.info("All handlers registered")
    
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
            logger.info("Starting bot...")
            self.app.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
            
        except TelegramError as e:
            logger.error(f"Telegram error: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            sys.exit(1)
        finally:
            if self.scheduler:
                self.scheduler.stop()

def main():
    """Main entry point"""
    logger.info("=" * 50)
    logger.info("Starting Telegram Bot with Advanced Features")
    logger.info("=" * 50)
    
    # Check if running on Railway
    if Config.BOT_TOKEN:
        logger.info("Configuration loaded successfully")
        logger.info(f"Features enabled: {', '.join([k for k, v in Config.FEATURES.items() if v])}")
    else:
        logger.warning("Running with minimal configuration")
    
    # Run bot
    bot = TelegramBot()
    bot.run()

if __name__ == "__main__":
    main()
