import asyncio
import os
import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, FSInputFile, ReplyKeyboardMarkup, KeyboardButton
from aiogram.enums import ParseMode

import config
import database as db
import api_handler as api

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❓ Help"), KeyboardButton(text="💎 Plan")],
            [KeyboardButton(text="🎁 Refer"), KeyboardButton(text="👤 My")]
        ], resize_keyboard=True, input_field_placeholder="Select an option or send a Terabox link..."
    )

async def get_missing_channels(user_id):
    missing = []
    channels = await db.get_all_fsubs()
    for ch in channels:
        try:
            member = await bot.get_chat_member(chat_id=ch['channel_id'], user_id=user_id)
            if member.status not in ['member', 'administrator', 'creator']: missing.append(ch)
        except: missing.append(ch)
    return missing

async def fsub_markup(missing_channels):
    markup = InlineKeyboardMarkup(inline_keyboard=[])
    for ch in missing_channels: markup.inline_keyboard.append([InlineKeyboardButton(text=f"❗ Join {ch['channel_id']} ✅", url=ch['channel_url'])])
    markup.inline_keyboard.append([InlineKeyboardButton(text="✅ Joined", callback_data="verify_join")])
    return markup

@dp.message(CommandStart())
async def send_welcome(message: types.Message):
    await db.get_user(message.from_user.id)
    missing = await get_missing_channels(message.from_user.id)
    if missing: return await message.answer("<b>Join Channel To Use This Bot</b>", reply_markup=await fsub_markup(missing), parse_mode=ParseMode.HTML)
    await message.answer("<b>Send Me TeraBox Links !</b>\n\nI will download or stream it for you instantly. 🚀", reply_markup=get_main_menu(), parse_mode=ParseMode.HTML)

@dp.callback_query(F.data == "verify_join")
async def verify_join_callback(call: types.CallbackQuery):
    missing = await get_missing_channels(call.from_user.id)
    if not missing:
        await call.message.delete()
        await call.message.answer("<b>Thank you for joining! 🎉</b>\n\n<b>Send Me TeraBox Links !</b>", reply_markup=get_main_menu(), parse_mode=ParseMode.HTML)
    else: await call.answer("You haven't joined all channels yet!", show_alert=True)

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    role = await db.get_admin_role(message.from_user.id)
    if not role: return
    railway_domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN")
    railway_url = f"https://{railway_domain}" if railway_domain else "http://localhost:8080"
    admin_url = f"{config.WEBAPP_URL}/admin/index.html?api={railway_url}"
    markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🌐 Open Admin Panel", web_app=WebAppInfo(url=admin_url))]])
    await message.answer("🔐 <b>Admin Dashboard</b>\n\nএখান থেকে সবকিছু কন্ট্রোল করুন:", reply_markup=markup, parse_mode=ParseMode.HTML)

@dp.message(F.text == "👤 My")
async def my_profile_handler(message: types.Message):
    user = await db.get_user(message.from_user.id)
    vip_status = "🌟 VIP Member" if user.get("vip", False) else "👤 Normal User"
    await message.answer(f"<b>Your Profile Information:</b>\n\n🆔 <b>User ID:</b> <code>{message.from_user.id}</code>\n🔰 <b>Position:</b> {vip_status}", parse_mode=ParseMode.HTML)

@dp.message(F.text == "❓ Help")
async def help_handler(message: types.Message):
    settings = await db.get_settings()
    text = "<b>📞 Help & Support Center</b>\n\nIf you need any assistance, feel free to contact us through our official channels below:\n"
    if settings.get("help_email"): text += f"\n📧 <b>Email:</b> {settings['help_email']}"
    if settings.get("help_fb"): text += f"\n📘 <b>Facebook:</b> {settings['help_fb']}"
    if settings.get("help_tg"): text += f"\n✈️ <b>Telegram:</b> {settings['help_tg']}"
    if settings.get("help_wa"): text += f"\n📱 <b>WhatsApp:</b> {settings['help_wa']}"
    if not any([settings.get("help_email"), settings.get("help_fb"), settings.get("help_tg"), settings.get("help_wa")]):
        text += "\n<i>No support channels configured yet.</i>"
    await message.answer(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

@dp.message(F.text == "💎 Plan")
async def plan_handler(message: types.Message):
    plans = await db.get_all_plans()
    if not plans: return await message.answer("<b>💎 VIP Subscription Plans</b>\n\nCurrently, there are no premium plans available.", parse_mode=ParseMode.HTML)
    markup = InlineKeyboardMarkup(inline_keyboard=[])
    for p in plans: markup.inline_keyboard.append([InlineKeyboardButton(text=f"💎 {p['name']} - {p['price']}", callback_data=f"buyplan_{p['plan_id']}")])
    await message.answer("<b>💎 VIP Subscription Plans</b>\n\nSelect a plan from below to see payment details:", reply_markup=markup, parse_mode=ParseMode.HTML)

@dp.callback_query(F.data.startswith("buyplan_"))
async def buy_plan_callback(call: types.CallbackQuery):
    plan_id = call.data.split("buyplan_")[1]
    plans = await db.get_all_plans()
    selected_plan = next((p for p in plans if p['plan_id'] == plan_id), None)
    if not selected_plan: return await call.answer("Plan not found!", show_alert=True)
    
    settings = await db.get_settings()
    pay_text = ""
    if settings.get("pay_bkash"): pay_text += f"🟣 <b>bKash:</b> <code>{settings['pay_bkash']}</code>\n"
    if settings.get("pay_nagad"): pay_text += f"🟠 <b>Nagad:</b> <code>{settings['pay_nagad']}</code>\n"
    if settings.get("pay_rocket"): pay_text += f"🚀 <b>Rocket:</b> <code>{settings['pay_rocket']}</code>\n"
    if settings.get("pay_crypto"): pay_text += f"🪙 <b>Crypto:</b> <code>{settings['pay_crypto']}</code>\n"
    if not pay_text: pay_text = "<i>No automated payment methods configured. Please contact admin.</i>\n"
    
    text = (f"🛒 <b>Checkout: {selected_plan['name']}</b>\n\n⏳ <b>Duration:</b> {selected_plan['duration']}\n💰 <b>Amount to Pay:</b> {selected_plan['price']}\n\n💳 <b>Payment Methods:</b>\n{pay_text}\n⚠️ <i>After sending the payment, please send a screenshot of the transaction to the Admin for VIP activation!</i>")
    markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Back to Plans", callback_data="back_to_plans")]])
    await call.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)

@dp.callback_query(F.data == "back_to_plans")
async def back_to_plans_callback(call: types.CallbackQuery):
    plans = await db.get_all_plans()
    markup = InlineKeyboardMarkup(inline_keyboard=[])
    for p in plans: markup.inline_keyboard.append([InlineKeyboardButton(text=f"💎 {p['name']} - {p['price']}", callback_data=f"buyplan_{p['plan_id']}")])
    await call.message.edit_text("<b>💎 VIP Subscription Plans</b>\n\nSelect a plan from below to see payment details:", reply_markup=markup, parse_mode=ParseMode.HTML)

@dp.message(F.text == "🎁 Refer")
async def refer_handler(message: types.Message):
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={message.from_user.id}"
    await message.answer(f"<b>🎁 Refer & Earn</b>\n\nShare this link with your friends:\n<code>{ref_link}</code>", parse_mode=ParseMode.HTML)

@dp.message(F.text.contains("terabox"))
async def handle_link(message: types.Message):
    missing = await get_missing_channels(message.from_user.id)
    if missing: return await message.answer("<b>Join Channel To Use This Bot</b>", reply_markup=await fsub_markup(missing), parse_mode=ParseMode.HTML)
    
    msg = await message.answer("⏳ Wait 2-4 Seconds...", reply_markup=get_main_menu())
    
    link, size, title = await api.get_terabox_direct_link(message.text, request_type="download")
    
    if not link:
        link, size, title = await api.get_terabox_direct_link(message.text, request_type="stream")
        if not link: return await msg.edit_text("❌ লিংকটি কাজ করছে না অথবা API ডাউন।")

    user = await db.get_user(message.from_user.id)
    is_vip = user.get("vip", False)
    
    if not is_vip and size and size > 50 * 1024 * 1024:
        player_url = f"{config.WEBAPP_URL}/player/player.html?link={link}&title={title}"
        markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="▶️ Watch & Download", web_app=WebAppInfo(url=player_url))]])
        return await msg.edit_text(f"📁 <b>{title}</b>\n\n⚠️ File is too large for Telegram (Max 50MB for Normal Users).\nWatch or Download directly below:", reply_markup=markup, parse_mode=ParseMode.HTML)
    
    await msg.edit_text("⏳ Downloading...")
    file_path = f"{message.from_user.id}.mp4"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(link) as resp:
                with open(file_path, 'wb') as f: f.write(await resp.read())
                await bot.send_video(message.chat.id, FSInputFile(file_path), caption=title)
                os.remove(file_path)
                await msg.delete()
    except:
        await msg.edit_text("❌ সমস্যা হয়েছে।")
        if os.path.exists(file_path): os.remove(file_path)

def cors_headers(): return {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "POST, GET, OPTIONS", "Access-Control-Allow-Headers": "Content-Type"}
async def options_handler(request): return web.Response(headers=cors_headers())

async def api_get_stats(request):
    raw_users = await db.get_all_users()
    subs = await db.get_all_fsubs()
    admins = await db.get_all_admins()
    settings = await db.get_settings()
    plans = await db.get_all_plans()
    
    unique_users = {}
    for u in raw_users:
        uid = u["user_id"]
        if uid not in unique_users or u.get("vip", False): unique_users[uid] = u
            
    users = list(unique_users.values())
    active_users = [u for u in users if u.get("is_active", True)]
    
    return web.json_response({
        "total_users": len(users), "active_users": len(active_users),
        "users_list": [{"id": u["user_id"], "vip": u.get("vip", False), "active": u.get("is_active", True)} for u in users],
        "subs": [{"id": s["channel_id"], "url": s["channel_url"]} for s in subs],
        "admins": [{"id": a["user_id"], "role": a["role"]} for a in admins],
        "settings": settings,
        "plans": [{"id": p["plan_id"], "name": p["name"], "duration": p["duration"], "price": p["price"]} for p in plans]
    }, headers=cors_headers())

async def api_update_settings(request):
    data = await request.json()
    await db.update_settings(data)
    return web.json_response({"status": "ok"}, headers=cors_headers())

async def api_add_custom_api(request):
    data = await request.json()
    await db.add_api(data['api_type'], data['api_url'])
    return web.json_response({"status": "ok"}, headers=cors_headers())

async def api_del_custom_api(request):
    data = await request.json()
    await db.del_api(data['api_type'], data['api_url'])
    return web.json_response({"status": "ok"}, headers=cors_headers())

# 🔴 Updated Smart API Test Logic (POST + GET)
async def api_test_custom_api(request):
    data = await request.json()
    api_url = data['api_url']
    test_tb_url = "https://1024terabox.com/s/1dummy"
    
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            # 1. Try POST first
            clean_api = api_url.split('?url=')[0]
            try:
                async with session.post(clean_api, json={"url": test_tb_url}, headers={"User-Agent": "Mozilla/5.0"}) as resp:
                    if resp.status in [200, 400, 403, 404, 500]: # If it responds with anything, it's alive
                        return web.json_response({"status": "Active"}, headers=cors_headers())
            except: pass
            
            # 2. Try GET if POST fails
            test_url = f"{api_url}{test_tb_url}" if api_url.endswith('=') else f"{api_url}?url={test_tb_url}"
            try:
                async with session.get(test_url, headers={"User-Agent": "Mozilla/5.0"}) as resp:
                    if resp.status in [200, 400, 403, 404, 500]:
                        return web.json_response({"status": "Active"}, headers=cors_headers())
            except: pass
            
    except Exception: pass
    
    return web.json_response({"status": "Dead"}, headers=cors_headers())

async def api_add_plan(request):
    data = await request.json()
    await db.add_plan(data['plan_id'], data['name'], data['duration'], data['price'])
    return web.json_response({"status": "ok"}, headers=cors_headers())

async def api_del_plan(request):
    data = await request.json()
    await db.remove_plan(data['plan_id'])
    return web.json_response({"status": "ok"}, headers=cors_headers())

async def api_toggle_vip(request):
    data = await request.json()
    await db.toggle_vip(int(data['user_id']), data['vip'])
    return web.json_response({"status": "ok"}, headers=cors_headers())

async def api_add_admin(request):
    data = await request.json()
    success = await db.add_new_admin(int(data['user_id']), data['role'])
    return web.json_response({"status": "ok" if success else "error"}, headers=cors_headers())

async def api_del_admin(request):
    data = await request.json()
    await db.remove_admin(int(data['user_id']))
    return web.json_response({"status": "ok"}, headers=cors_headers())

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
    b_type = data.get('type', 'all')
    msg = data['message']
    
    if b_type == 'specific':
        try: await bot.send_message(int(data['target_id']), msg)
        except: pass
    else:
        raw_users = await db.get_all_users()
        unique_users = {}
        for u in raw_users:
            uid = u["user_id"]
            if uid not in unique_users or u.get("vip", False): unique_users[uid] = u
                
        for u in unique_users.values():
            if b_type == 'vip' and not u.get('vip', False): continue
            try:
                await bot.send_message(u['user_id'], msg)
                await db.update_user_status(u['user_id'], True)
                await asyncio.sleep(0.05)
            except:
                await db.update_user_status(u['user_id'], False)
    return web.json_response({"status": "ok"}, headers=cors_headers())

async def web_server():
    app = web.Application()
    app.router.add_options('/api/{tail:.*}', options_handler)
    app.router.add_get('/api/stats', api_get_stats)
    app.router.add_post('/api/update_settings', api_update_settings)
    app.router.add_post('/api/add_plan', api_add_plan) 
    app.router.add_post('/api/del_plan', api_del_plan) 
    app.router.add_post('/api/add_api', api_add_custom_api)
    app.router.add_post('/api/del_api', api_del_custom_api)
    app.router.add_post('/api/test_api', api_test_custom_api)
    app.router.add_post('/api/toggle_vip', api_toggle_vip)
    app.router.add_post('/api/add_admin', api_add_admin)
    app.router.add_post('/api/del_admin', api_del_admin)
    app.router.add_post('/api/add_sub', api_add_sub)
    app.router.add_post('/api/del_sub', api_del_sub)
    app.router.add_post('/api/broadcast', api_broadcast)
    
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 8080))).start()

async def main():
    await db.init_db()
    await bot.delete_webhook(drop_pending_updates=True) 
    await asyncio.gather(dp.start_polling(bot), web_server())

if __name__ == "__main__":
    asyncio.run(main())
