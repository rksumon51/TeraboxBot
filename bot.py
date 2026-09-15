import asyncio
import os
import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, FSInputFile
from aiogram.enums import ParseMode

import config
import database as db
import api_handler as api

# বট এবং ডিসপ্যাচার ইনিশিয়ালাইজেশন (Aiogram 3.x)
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

# ==========================================
# বটের কমান্ডস (Bot Commands)
# ==========================================

@dp.message(CommandStart())
async def send_welcome(message: types.Message):
    """ইউজার /start দিলে এই মেসেজ যাবে"""
    user_id = message.from_user.id
    await db.get_user(user_id) # ডেটাবেসে ইউজার সেভ বা আপডেট করবে
    
    text = (
        "👋 <b>Terabox Video Bot-এ স্বাগতম!</b>\n\n"
        "যেকোনো Terabox লিংক দিন, ভিডিও যদি ৫০ এমবির কম হয় তবে আমি সরাসরি ফাইল পাঠাবো, "
        "আর বড় হলে সরাসরি দেখার/ডাউনলোডের লিংক দিবো।"
    )
    await message.answer(text, parse_mode=ParseMode.HTML)

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    """অ্যাডমিনদের জন্য ওয়েব প্যানেল বাটন"""
    user_id = message.from_user.id
    role = await db.get_admin_role(user_id)
    
    if not role:
        return # সাধারণ ইউজারদের জন্য কোনো রেসপন্স করবে না
        
    admin_url = f"{config.WEBAPP_URL}/admin/index.html"
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 Open Web Panel", web_app=WebAppInfo(url=admin_url))]
    ])
    
    await message.answer(f"🔐 <b>Admin Dashboard</b>\nআপনার রোল: {role}", reply_markup=markup, parse_mode=ParseMode.HTML)

# ==========================================
# লিংক প্রসেসিং লজিক (Video Handling)
# ==========================================

@dp.message(F.text.contains("terabox"))
async def handle_terabox_link(message: types.Message):
    """ইউজার Terabox লিংক দিলে এটি প্রসেস করবে"""
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    
    # লিমিট চেক (ফ্রি ইউজারদের জন্য)
    if not user['is_premium']:
        settings = await db.settings_col.find_one({"_id": "global_settings"})
        daily_limit = settings['daily_free_limit']
        if user.get('daily_links', 0) >= daily_limit:
            await message.answer("⚠️ আপনার আজকের ফ্রি লিমিট শেষ! দয়া করে সাবস্ক্রিপশন কিনুন।")
            return
            
    processing_msg = await message.answer("⏳ লিংকটি প্রসেস করা হচ্ছে...")
    
    # API থেকে ডাইরেক্ট লিংক ও সাইজ বের করা
    direct_link, size_bytes, title = await api.get_terabox_direct_link(message.text)
    
    if not direct_link:
        await processing_msg.edit_text("❌ দুঃখিত, ভিডিওটি বের করা সম্ভব হয়নি। লিংকটি সঠিক কিনা চেক করুন।")
        return
        
    # ফ্রি ইউজার হলে ডেটাবেসে লিমিট কাউন্ট +১ করে দেওয়া
    if not user['is_premium']:
        await db.users_col.update_one({"user_id": user_id}, {"$inc": {"daily_links": 1}})

    # সাইজ চেক লজিক (৫০ মেগাবাইট)
    MAX_SIZE = 50 * 1024 * 1024 # 50 MB
    
    if size_bytes and size_bytes <= MAX_SIZE:
        await processing_msg.edit_text("⬇️ ভিডিও ডাউনলোড হচ্ছে, একটু অপেক্ষা করুন...")
        file_path = f"{user_id}_video.mp4"
        
        # ভিডিও সার্ভারে ডাউনলোড করা
        async with aiohttp.ClientSession() as session:
            async with session.get(direct_link) as resp:
                if resp.status == 200:
                    with open(file_path, 'wb') as f:
                        f.write(await resp.read())
                        
                    await processing_msg.edit_text("📤 ভিডিও টেলিগ্রামে আপলোড করা হচ্ছে...")
                    
                    # টেলিগ্রামে ফাইল পাঠানো
                    video_file = FSInputFile(file_path)
                    await bot.send_video(chat_id=message.chat.id, video=video_file, caption=f"🎬 <b>{title}</b>", parse_mode=ParseMode.HTML)
                    
                    # আপলোড শেষে সার্ভার থেকে ফাইল মুছে ফেলা
                    os.remove(file_path)
                    await processing_msg.delete()
                else:
                    await processing_msg.edit_text("❌ সার্ভার থেকে ফাইল ডাউনলোডে সমস্যা হয়েছে।")
    else:
        # ৫০ এমবির বেশি হলে Web App প্লেয়ার লিংক দেওয়া
        player_url = f"{config.WEBAPP_URL}/player/player.html?link={direct_link}&title={title}"
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="▶️ Watch & Download", web_app=WebAppInfo(url=player_url))]
        ])
        
        text = (
            f"🎬 <b>{title}</b>\n\n"
            "⚠️ <i>ভিডিওটি ৫০ এমবির চেয়ে বড়। তাই সরাসরি দেখতে বা ডাউনলোড করতে নিচের বাটনে ক্লিক করুন:</i>"
        )
        await processing_msg.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)

# ==========================================
# ওয়েব সার্ভার ও মেইন রানার (Web Server & Runner)
# ==========================================

async def web_server():
    """aiohttp ওয়েব সার্ভার যা আপনার ওয়েবসাইট হোস্ট করবে"""
    app = web.Application()
    
    # ফোল্ডারগুলো না থাকলে তৈরি করবে (ক্র্যাশ রোধ করতে)
    os.makedirs("web/admin", exist_ok=True)
    os.makedirs("web/player", exist_ok=True)
    
    # স্ট্যাটিক ফোল্ডার রাউটিং
    app.router.add_static('/admin', 'web/admin', name='admin')
    app.router.add_static('/player', 'web/player', name='player')
    
    # মেইন ডোমেইন হিট করলে মেসেজ দেখাবে
    async def index(request):
        return web.Response(text="✅ Terabox Bot & Web Server is Running!")
    app.router.add_get('/', index)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    print("🌐 Web Server is running on http://0.0.0.0:8080")

async def main():
    """বট এবং ওয়েব সার্ভার একসাথে চালু করার ফাংশন"""
    await db.init_db() # ডেটাবেস ইনিশিয়ালাইজেশন
    print("🤖 Telegram Bot is starting...")
    
    # asyncio.gather দিয়ে দুটো প্রসেস একসাথে চালানো হচ্ছে
    await asyncio.gather(
        dp.start_polling(bot),
        web_server()
    )

if __name__ == "__main__":
    asyncio.run(main())
