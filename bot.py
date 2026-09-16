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

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

# === Force Subscribe Logic ===
async def get_missing_channels(user_id):
    missing = []
    channels = await db.get_all_fsubs()
    for ch in channels:
        try:
            member = await bot.get_chat_member(chat_id=ch['channel_id'], user_id=user_id)
            if member.status not in ['member', 'administrator', 'creator']: 
                missing.append(ch)
        except: 
            missing.append(ch)
    return missing

async def fsub_markup(missing_channels):
    markup = InlineKeyboardMarkup(inline_keyboard=[])
    for ch in missing_channels:
        markup.inline_keyboard.append([InlineKeyboardButton(text=f"❗ Join {ch['channel_id']} ✅", url=ch['channel_url'])])
    markup.inline_keyboard.append([InlineKeyboardButton(text="✅ Joined", callback_data="verify_join")])
    return markup

# === Bot Commands ===
@dp.message(CommandStart())
async def send_welcome(message: types.Message):
    await db.get_user(message.from_user.id)
    missing = await get_missing_channels(message.from_user.id)
    if missing:
        markup = await fsub_markup(missing)
        await message.answer("<b>Join Channel To Use This Bot</b>", reply_markup=markup, parse_mode=ParseMode.HTML)
        return
    text = ("<b>Send Me TeraBox Links</b>\n\n/videos use This For Videos\n/videos use This For Videos\n\n<b>For TeraBox Links ❤️</b>")
    await message.answer(text, parse_mode=ParseMode.HTML)

@dp.callback_query(F.data == "verify_join")
async def verify_join_callback(call: types.CallbackQuery):
    missing = await get_missing_channels(call.from_user.id)
    if not missing:
        text = ("<b>Send Me TeraBox Links</b>\n\n/videos use This For Videos\n/videos use This For Videos\n\n<b>For TeraBox Links ❤️</b>")
        await call.message.edit_text(text, parse_mode=ParseMode.HTML)
    else:
        await call.answer("You haven't joined all channels yet!", show_alert=True)

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    role = await db.get_admin_role(message.from_user.id)
    if not role: return
    
    railway_domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN")
    railway_url = f"https://{railway_domain}" if railway_domain else "http://localhost:8080"
    
    admin_url = f"{config.WEBAPP_URL}/admin/index.html?api={railway_url}"
    markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🌐 Open Admin Panel", web_app=WebAppInfo(url=admin_url))]])
    await message.answer("🔐 <b>Admin Dashboard</b>\n\nএখান থেকে সবকিছু কন্ট্রোল করুন:", reply_markup=markup, parse_mode=ParseMode.HTML)

# === Terabox Link Handler ===
@dp.message(F.text.contains("terabox"))
async def handle_link(message: types.Message):
    missing = await get_missing_channels(message.from_user.id)
    if missing:
        await message.answer("<b>Join Channel To Use This Bot</b>", reply_markup=await fsub_markup(missing), parse_mode=ParseMode.HTML)
        return
    msg = await message.answer("⏳ Wait 2-4 Seconds.")
    link, size, title = await api.get_terabox_direct_link(message.text)
    
    if not link:
        await msg.edit_text("❌ লিংকটি কাজ করছে না।")
        return
        
    if size and size <= 50 * 1024 * 1024:
        await msg.edit_text("⏳ Downloading...")
        file_path = f"{message.from_user.id}.mp4"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(link) as resp:
                    with open(file_path, 'wb') as f: 
                        f.write(await resp.read())
                    await bot.send_video(message.chat.id, FSInputFile(file_path), caption=title)
                    os.remove(file_path)
                    await msg.delete()
        except:
            await msg.edit_text("❌ সমস্যা হয়েছে।")
            if os.path.exists(file_path): 
                os.remove(file_path)
    else:
        player_url = f"{config.WEBAPP_URL}/player/player.html?link={link}&title={title}"
        markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="▶️ Watch & Download", web_app=WebAppInfo(url=player_url))]])
        await msg.edit_text(f"📁 <b>{title}</b>\n\n⚠️ File is too large. Watch below:", reply_markup=markup, parse_mode=ParseMode.HTML)

# === API Routes for Web Panel ===
def cors_headers(): 
    return {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "POST, GET, OPTIONS", "Access-Control-Allow-Headers": "Content-Type"}

async def options_handler(request): 
    return web.Response(headers=cors_headers())

async def api_get_stats(request):
    users = await db.get_total_users()
    subs = await db.get_all_fsubs()
    return web.json_response({"users": users, "subs": [{"id": s["channel_id"], "url": s["channel_url"]} for s in subs]}, headers=cors_headers())

async def api_add_sub(request):
    data = await request.json()
    await db.add_fsub(data['channel_id'], data['channel_url'])
    return web.json_response({"status": "ok"}, headers=cors_headers())

async def api_del_sub(request):
    data = await request.json()
    await db.remove_fsub(data['channel_id'])
    return web.json_response({"status": "ok"}, headers=cors_headers())

async def api_broadcast(request):
    data = await request.json()
    users = await db.get_all_users()
    for u in users:
        try:
            await bot.send_message(u['user_id'], data['message'])
            await asyncio.sleep(0.05)
        except: pass
    return web.json_response({"status": "ok"}, headers=cors_headers())

async def api_add_admin(request):
    data = await request.json()
    success = await db.add_new_admin(int(data['user_id']), data['role'])
    if success:
        return web.json_response({"status": "ok"}, headers=cors_headers())
    return web.json_response({"status": "error"}, headers=cors_headers())

async def web_server():
    app = web.Application()
    app.router.add_options('/api/{tail:.*}', options_handler)
    app.router.add_get('/api/stats', api_get_stats)
    app.router.add_post('/api/add_sub', api_add_sub)
    app.router.add_post('/api/del_sub', api_del_sub)
    app.router.add_post('/api/broadcast', api_broadcast)
    app.router.add_post('/api/add_admin', api_add_admin)
    
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 8080))).start()

# === Main Execution ===
async def main():
    await db.init_db()
    
    # 🔥 আগের সব আটকে থাকা কানেকশন ক্লিয়ার করার কোড (TelegramConflictError ফিক্স)
    await bot.delete_webhook(drop_pending_updates=True) 
    
    await asyncio.gather(dp.start_polling(bot), web_server())

if __name__ == "__main__":
    asyncio.run(main())
