import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Bot Token
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///bot_database.db')
    
    # Admin IDs (Super Admin)
    SUPER_ADMIN_IDS = list(map(int, os.getenv('SUPER_ADMIN_IDS', '').split(','))) if os.getenv('SUPER_ADMIN_IDS') else []
    
    # Bot Settings
    BOT_USERNAME = os.getenv('BOT_USERNAME')
    DEFAULT_LANGUAGE = os.getenv('DEFAULT_LANGUAGE', 'id')
    
    # Channel/Group IDs untuk Auto Post
    AUTO_POST_CHANNELS = list(map(int, os.getenv('AUTO_POST_CHANNELS', '').split(','))) if os.getenv('AUTO_POST_CHANNELS') else []
    
    # Welcome Settings
    WELCOME_CHANNELS = list(map(int, os.getenv('WELCOME_CHANNELS', '').split(','))) if os.getenv('WELCOME_CHANNELS') else []
    
    # Feature Flags
    FEATURES = {
        'auto_welcome': os.getenv('FEATURE_AUTO_WELCOME', 'true').lower() == 'true',
        'auto_post': os.getenv('FEATURE_AUTO_POST', 'true').lower() == 'true',
        'broadcast': os.getenv('FEATURE_BROADCAST', 'true').lower() == 'true',
        'user_tracking': os.getenv('FEATURE_USER_TRACKING', 'true').lower() == 'true',
        'multi_language': os.getenv('FEATURE_MULTI_LANGUAGE', 'true').lower() == 'true',
    }
