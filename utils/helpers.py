import json
import os
from datetime import datetime, timedelta
import pytz
from typing import Dict, Any
from database import get_db, Setting

def load_language(lang_code: str) -> Dict:
    """Load language file"""
    try:
        with open(f'languages/{lang_code}.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        with open('languages/en.json', 'r', encoding='utf-8') as f:
            return json.load(f)

def get_text(user_id: int, key: str, **kwargs) -> str:
    """Get text in user's language"""
    db = next(get_db())
    from database import User
    
    user = db.query(User).filter_by(user_id=user_id).first()
    lang = user.language if user else 'id'
    
    texts = load_language(lang)
    text = texts.get(key, key)
    
    # Format with kwargs
    if kwargs:
        text = text.format(**kwargs)
    
    return text

def get_setting(key: str, default: Any = None) -> Any:
    """Get setting value"""
    db = next(get_db())
    setting = db.query(Setting).filter_by(key=key).first()
    return setting.value if setting else default

def format_number(num: int) -> str:
    """Format number with thousand separator"""
    return f"{num:,}".replace(",", ".")

def parse_time(time_str: str) -> datetime.time:
    """Parse time string to time object"""
    try:
        return datetime.strptime(time_str, "%H:%M").time()
    except:
        return None

def get_wib_time():
    """Get current time in WIB"""
    tz = pytz.timezone('Asia/Jakarta')
    return datetime.now(tz)

def chunk_list(lst, n):
    """Split list into chunks of size n"""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
