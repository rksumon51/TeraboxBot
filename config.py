import os
from dotenv import load_dotenv

# .env ফাইল থাকলে সেখান থেকে ডাটা লোড করবে
load_dotenv()

# os.getenv("ভেরিয়েবলের_নাম", "যদি_না_পায়_তবে_এটি_ব্যবহার_করবে")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8616358877:AAHJdquziRgvrOVgDNQgLa-TZ1xNl8evQvk")
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://admin:5129534Yk@cluster0.0ggumii.mongodb.net/?appName=Cluster0")
PRIMARY_OWNER_ID = int(os.getenv("PRIMARY_OWNER_ID", 8110034101))
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://terabox-bot-steel.vercel.app")
