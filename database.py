from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import config

client = AsyncIOMotorClient(config.MONGO_URI)
db = client['TeraboxBotDB']

users_col = db['users']
admins_col = db['admins']
fsub_col = db['force_subs']

async def init_db():
    owner = await admins_col.find_one({"user_id": config.PRIMARY_OWNER_ID})
    if not owner:
        await admins_col.insert_one({"user_id": config.PRIMARY_OWNER_ID, "role": "Primary Owner"})

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

async def get_all_users(): 
    return await users_col.find({}).to_list(length=None)

async def update_user_status(user_id, is_active):
    await users_col.update_one({"user_id": user_id}, {"$set": {"is_active": is_active}})

async def toggle_vip(user_id, vip_status):
    await users_col.update_one({"user_id": user_id}, {"$set": {"vip": vip_status}})

async def get_all_admins():
    return await admins_col.find({}).to_list(length=None)

async def add_new_admin(user_id, role="Co-Owner"):
    if not await admins_col.find_one({"user_id": user_id}):
        await admins_col.insert_one({"user_id": user_id, "role": role})
        return True
    return False

async def remove_admin(user_id):
    await admins_col.delete_one({"user_id": user_id})

async def add_fsub(channel_id, channel_url):
    await fsub_col.update_one({"channel_id": channel_id}, {"$set": {"channel_url": channel_url}}, upsert=True)

async def remove_fsub(channel_id):
    await fsub_col.delete_one({"channel_id": channel_id})

async def get_all_fsubs():
    return await fsub_col.find({}).to_list(length=None)
