import os
from dotenv import load_dotenv

# .env ফাইল থাকলে সেখান থেকে ডাটা লোড করবে
load_dotenv()

# os.getenv("ভেরিয়েবলের_নাম", "যদি_না_পায়_তবে_এটি_ব্যবহার_করবে")
BOT_TOKEN = os.getenv("BOT_TOKEN", "এখানে_আপনার_আসল_টোকেন_দিন")
MONGO_URI = os.getenv("MONGO_URI", "এখানে_আপনার_মঙ্গোডিবি_লিংক_দিন")
PRIMARY_OWNER_ID = int(os.getenv("PRIMARY_OWNER_ID", 8110034101))
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://terabox-bot-steel.vercel.app")
