import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# MongoDB
MONGODB_URI = os.getenv('MONGODB_URI')

# Admin IDs
ADMIN_IDS = list(map(int, os.getenv('ADMIN_IDS', '').split(',')))


ALLOWED_DIRS = ["/"]

# Здесь можете указать разрешённые папки для операций с директориями.

DANGER_DIRS = [
    
]

ALLOWED_EXTENSIONS = [

]

    # ".txt", ".py", ".js", ".json", ".xml", ".yaml", ".yml",
    # ".png",".jpg",".jpeg",".gif",".bmp",".svg",".mp4",".avi",".mkv",".pdf",".docx",".xlsx",
    # ".env",
    # ".html", ".css", ".md", ".log", ".conf", ".ini", ".cfg"