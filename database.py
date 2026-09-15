from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
import config

# MongoDB কানেকশন
client = AsyncIOMotorClient(config.MONGO_URI)
db = client['TeraboxBotDB']

# Collections (ডেটাবেসের ফোল্ডারসমূহ)
users_col = db['users']
admins_col = db['admins']
channels_col = db['channels']
settings_col = db['settings']

# ==========================================
# ইনিশিয়ালাইজেশন (Primary Owner ও Settings)
# ==========================================
async def init_db():
    """বট চালু হলে ডিফল্ট সেটিংস এবং Primary Owner সেট করবে"""
    # Primary Owner সেট করা (লকড)
    owner = await admins_col.find_one({"user_id": config.PRIMARY_OWNER_ID})
    if not owner:
        await admins_col.insert_one({"user_id": config.PRIMARY_OWNER_ID, "role": "Primary Owner"})
    
    # বটের ডিফল্ট গ্লোবাল সেটিংস
    settings = await settings_col.find_one({"_id": "global_settings"})
    if not settings:
        await settings_col.insert_one({
            "_id": "global_settings",
            "fsub_enabled": False,          # Force Sub বন্ধ
            "sub_system_enabled": True,     # Subscription সিস্টেম চালু
            "daily_free_limit": 3           # ফ্রি ইউজারদের জন্য দিনে ৩টি ভিডিও
        })

# ==========================================
# অ্যাডমিন রোল কন্ট্রোল 
# ==========================================
async def get_admin_role(user_id):
    """চেক করবে ইউজারের রোল কী (Primary Owner, Manager, Editor)"""
    if user_id == config.PRIMARY_OWNER_ID:
        return "Primary Owner"
    admin = await admins_col.find_one({"user_id": user_id})
    return admin['role'] if admin else None

# ==========================================
# ইউজার ও সাবস্ক্রিপশন লজিক
# ==========================================
async def get_user(user_id):
    """ইউজার না থাকলে ডেটাবেসে এড করবে এবং নতুন দিনে লিমিট রিসেট করবে"""
    user = await users_col.find_one({"user_id": user_id})
    today = datetime.utcnow().strftime('%Y-%m-%d')
    
    if not user:
        user = {
            "user_id": user_id,
            "is_premium": False,
            "premium_expiry": None,
            "daily_links": 0,
            "last_active": today
        }
        await users_col.insert_one(user)
    else:
        # নতুন দিন শুরু হলে লিমিট জিরো (0) করে দিবে
        if user.get("last_active") != today:
            await users_col.update_one(
                {"user_id": user_id},
                {"$set": {"daily_links": 0, "last_active": today}}
            )
            user["daily_links"] = 0
            
    return user

async def add_subscription(user_id, days):
    """ইউজারকে প্রিমিয়াম দিবে (1, 7, 30 বা lifetime)"""
    if str(days).lower() == "lifetime":
        expiry = "Lifetime"
    else:
        expiry_date = datetime.utcnow() + timedelta(days=int(days))
        expiry = expiry_date.strftime('%Y-%m-%d %H:%M:%S')
        
    await users_col.update_one(
        {"user_id": user_id},
        {"$set": {"is_premium": True, "premium_expiry": expiry}},
        upsert=True
    )
