import os
from dotenv import load_dotenv

# .env ফাইল লোড করা
load_dotenv()

# ভেরিয়েবলগুলো সেট করা
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
# String কে Integer এ রূপান্তর করছি, কারণ Telegram ID সবসময় নম্বর হয়
PRIMARY_OWNER_ID = int(os.getenv("PRIMARY_OWNER_ID", 0))
WEBAPP_URL = os.getenv("WEBAPP_URL", "")

# টোকেন মিসিং থাকলে বট রান হওয়ার আগেই ওয়ার্নিং দিবে
if not BOT_TOKEN or not MONGO_URI or PRIMARY_OWNER_ID == 0:
    raise ValueError("⚠️ .env ফাইলে BOT_TOKEN, MONGO_URI বা PRIMARY_OWNER_ID মিসিং আছে!")
