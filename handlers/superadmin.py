from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import pytz
from database import get_db, AutoPost, Broadcast
from telegram import Bot
import asyncio
import logging

logger = logging.getLogger(__name__)

class BotScheduler:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler(timezone=pytz.timezone('Asia/Jakarta'))
        self.setup_jobs()
    
    def setup_jobs(self):
        """Setup scheduled jobs"""
        # Check auto posts every minute
        self.scheduler.add_job(
            self.check_auto_posts,
            'interval',
            minutes=1,
            id='check_auto_posts'
        )
        
        # Check scheduled broadcasts every minute
        self.scheduler.add_job(
            self.check_scheduled_broadcasts,
            'interval',
            minutes=1,
            id='check_broadcasts'
        )
        
        # Daily backup at 3 AM
        self.scheduler.add_job(
            self.daily_backup,
            CronTrigger(hour=3, minute=0, timezone=pytz.timezone('Asia/Jakarta')),
            id='daily_backup'
        )
        
        # Clean old logs every week
        self.scheduler.add_job(
            self.clean_old_logs,
            CronTrigger(day_of_week='mon', hour=4, minute=0, timezone=pytz.timezone('Asia/Jakarta')),
            id='clean_logs'
        )
    
    async def check_auto_posts(self):
        """Check and execute scheduled auto posts"""
        try:
            db = next(get_db())
            now = datetime.now(pytz.timezone('Asia/Jakarta'))
            current_time = now.strftime("%H:%M")
            current_day = now.weekday()  # 0 = Monday
            
            posts = db.query(AutoPost).filter_by(
                is_active=True
            ).all()
            
            for post in posts:
                if post.schedule_time != current_time:
                    continue
                
                # Check if scheduled for today
                days = json.loads(post.schedule_days) if post.schedule_days else [0,1,2,3,4,5,6]
                if current_day not in days:
                    continue
                
                # Send post
                try:
                    await self.bot.send_message(
                        chat_id=post.channel_id,
                        text=post.message_text,
                        parse_mode='Markdown'
                    )
                    
                    post.last_posted = datetime.utcnow()
                    logger.info(f"Auto post sent to channel {post.channel_id}")
                except Exception as e:
                    logger.error(f"Failed to send auto post: {e}")
            
            db.commit()
        except Exception as e:
            logger.error(f"Error in check_auto_posts: {e}")
    
    async def check_scheduled_broadcasts(self):
        """Check and execute scheduled broadcasts"""
        try:
            db = next(get_db())
            now = datetime.utcnow()
            
            broadcasts = db.query(Broadcast).filter(
                Broadcast.status == 'pending',
                Broadcast.scheduled_time <= now
            ).all()
            
            for broadcast in broadcasts:
                # Mark as sending
                broadcast.status = 'sending'
                db.commit()
                
                # Send broadcast (would need to implement actual sending)
                # This is handled by broadcast handler
                
        except Exception as e:
            logger.error(f"Error in check_scheduled_broadcasts: {e}")
    
    async def daily_backup(self):
        """Perform daily database backup"""
        try:
            # Create backup (implementation depends on database type)
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"auto_backup_{timestamp}.db"
            
            db = next(get_db())
            from database import DatabaseBackup
            
            backup = DatabaseBackup(
                filename=filename,
                created_at=datetime.utcnow(),
                created_by=0,  # System backup
                size=0
            )
            db.add(backup)
            db.commit()
            
            logger.info(f"Daily backup created: {filename}")
        except Exception as e:
            logger.error(f"Daily backup failed: {e}")
    
    async def clean_old_logs(self):
        """Clean logs older than 30 days"""
        try:
            db = next(get_db())
            from database import AdminLog
            from datetime import timedelta
            
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            deleted = db.query(AdminLog).filter(
                AdminLog.timestamp < thirty_days_ago
            ).delete()
            
            db.commit()
            logger.info(f"Cleaned {deleted} old logs")
        except Exception as e:
            logger.error(f"Log cleanup failed: {e}")
    
    def start(self):
        """Start the scheduler"""
        self.scheduler.start()
        logger.info("Scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")
