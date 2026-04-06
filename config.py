import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_TOKEN_HERE")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "123456789").split(",")))

# Railway auto-detects PORT, use webhook if set, else polling
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")  # e.g. https://yourapp.up.railway.app
PORT = int(os.getenv("PORT", 8080))

# Paths - relative to project root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR = os.path.join(BASE_DIR, "media")
DB_PATH = os.path.join(BASE_DIR, "data", "bot.db")
