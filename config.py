import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Bot Token - REQUIRED
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    BOT_USERNAME = os.getenv('BOT_USERNAME', 'my_bot')
    
    # Database - Railway provides DATABASE_URL automatically
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///bot_database.db')
    
    # Admin IDs (Super Admin) - REQUIRED at least one
    try:
        SUPER_ADMIN_IDS = list(map(int, filter(None, os.getenv('SUPER_ADMIN_IDS', '').split(','))))
    except:
        SUPER_ADMIN_IDS = []
    
    # Channel/Group IDs for Auto Post
    try:
        AUTO_POST_CHANNELS = list(map(int, filter(None, os.getenv('AUTO_POST_CHANNELS', '').split(','))))
    except:
        AUTO_POST_CHANNELS = []
    
    # Welcome Channels
    try:
        WELCOME_CHANNELS = list(map(int, filter(None, os.getenv('WELCOME_CHANNELS', '').split(','))))
    except:
        WELCOME_CHANNELS = []
    
    # Bot Settings
    DEFAULT_LANGUAGE = os.getenv('DEFAULT_LANGUAGE', 'id')
    
    # Feature Flags (default to True if not specified)
    FEATURES = {
        'auto_welcome': os.getenv('FEATURE_AUTO_WELCOME', 'true').lower() == 'true',
        'auto_post': os.getenv('FEATURE_AUTO_POST', 'true').lower() == 'true',
        'broadcast': os.getenv('FEATURE_BROADCAST', 'true').lower() == 'true',
        'user_tracking': os.getenv('FEATURE_USER_TRACKING', 'true').lower() == 'true',
        'multi_language': os.getenv('FEATURE_MULTI_LANGUAGE', 'true').lower() == 'true',
    }
