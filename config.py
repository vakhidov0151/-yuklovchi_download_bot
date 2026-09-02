import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not BOT_TOKEN or BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
    raise ValueError("BOT_TOKEN is missing or not set in the .env file.")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is missing or not set in the .env file.")

# Majburiy obuna kanallari (virgul bilan ajratib yozing: @kanal1,@kanal2)
req_channels_env = os.getenv("REQUIRED_CHANNELS", "")
REQUIRED_CHANNELS = [ch.strip() for ch in req_channels_env.split(",") if ch.strip()]

# Admin(lar) ID
admin_env = os.getenv("ADMIN_ID", "")
ADMIN_IDS = [int(aid.strip()) for aid in admin_env.split(",") if aid.strip().isdigit()]

# To'lov ma'lumotlari (Karta orqali VIP)
CARD_NUMBER = os.getenv("CARD_NUMBER", "8600 1234 5678 9012")
CARD_OWNER = os.getenv("CARD_OWNER", "Falonchiyev Pistonchi")
VIP_PRICE = "15,000 so'm"
