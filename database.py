from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import config

client = AsyncIOMotorClient(config.MONGO_URI)
db = client['TeraboxBotDB']

users_col = db['users']
admins_col = db['admins']
fsub_col = db['force_subs']
settings_col = db['settings']
plans_col = db['plans']

async def init_db():
    owner = await admins_col.find_one({"user_id": config.PRIMARY_OWNER_ID})
    if not owner:
        await admins_col.insert_one({"user_id": config.PRIMARY_OWNER_ID, "role": "Primary Owner"})
    
    settings = await settings_col.find_one({"_id": "bot_settings"})
    if not settings:
        await settings_col.insert_one({
            "_id": "bot_settings", 
            "help_email": "", "help_fb": "", "help_tg": "", "help_wa": "",
            "pay_bkash": "", "pay_nagad": "", "pay_rocket": "", "pay_crypto": "",
            "download_apis": ["https://teraboxvideodownloader.nepcoderdevs.workers.dev/?url="], # Default API
            "stream_apis": ["https://teraboxvideodownloader.nepcoderdevs.workers.dev/?url="]    # Default API
        })

async def get_admin_role(user_id):
    if user_id == config.PRIMARY_OWNER_ID: return "Primary Owner"
    admin = await admins_col.find_one({"user_id": user_id})
    return admin['role'] if admin else None

async def get_user(user_id):
    user = await users_col.find_one({"user_id": user_id})
    if not user:
        user = {"user_id": user_id, "joined_date": datetime.utcnow().strftime('%Y-%m-%d'), "vip": False, "is_active": True}
        await users_col.insert_one(user)
    return user

async def get_all_users(): return await users_col.find({}).to_list(length=None)
async def update_user_status(user_id, is_active): await users_col.update_one({"user_id": user_id}, {"$set": {"is_active": is_active}})
async def toggle_vip(user_id, vip_status): await users_col.update_one({"user_id": user_id}, {"$set": {"vip": vip_status}})

async def get_all_admins(): return await admins_col.find({}).to_list(length=None)
async def add_new_admin(user_id, role="Co-Owner"):
    if not await admins_col.find_one({"user_id": user_id}):
        await admins_col.insert_one({"user_id": user_id, "role": role})
        return True
    return False
async def remove_admin(user_id): await admins_col.delete_one({"user_id": user_id})

async def add_fsub(channel_id, channel_url): await fsub_col.update_one({"channel_id": channel_id}, {"$set": {"channel_url": channel_url}}, upsert=True)
async def remove_fsub(channel_id): await fsub_col.delete_one({"channel_id": channel_id})
async def get_all_fsubs(): return await fsub_col.find({}).to_list(length=None)

async def get_settings():
    settings = await settings_col.find_one({"_id": "bot_settings"})
    return settings or {}

async def update_settings(data):
    await settings_col.update_one({"_id": "bot_settings"}, {"$set": data}, upsert=True)

# 🔴 API Management
async def add_api(api_type, api_url):
    await settings_col.update_one({"_id": "bot_settings"}, {"$addToSet": {api_type: api_url}})

async def del_api(api_type, api_url):
    await settings_col.update_one({"_id": "bot_settings"}, {"$pull": {api_type: api_url}})

async def add_plan(plan_id, name, duration, price): await plans_col.update_one({"plan_id": plan_id}, {"$set": {"name": name, "duration": duration, "price": price}}, upsert=True)
async def remove_plan(plan_id): await plans_col.delete_one({"plan_id": plan_id})
async def get_all_plans(): return await plans_col.find({}).to_list(length=None)
