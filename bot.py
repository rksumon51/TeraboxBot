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

# === 🔥 Dynamic Force Sub Checker ===
async def get_missing_channels(user_id):
    missing = []
    channels = await db.get_all_fsubs()
    for ch in channels:
        try:
            member = await bot.get_chat_member(chat_id=ch['channel_id'], user_id=user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                missing.append(ch)
        except:
            missing.append(ch) # বট যদি চ্যানেলে না থাকে বা ইউজার না থাকে
    return missing

async def fsub_markup(missing_channels):
    markup = InlineKeyboardMarkup(inline_keyboard=[])
    for ch in missing_channels:
        markup.inline_keyboard.append([InlineKeyboardButton(text=f"❗ Join {ch['channel_id']} ✅", url=ch['channel_url'])])
    markup.inline_keyboard.append([InlineKeyboardButton(text="✅ Joined", callback_data="verify_join")])
    return markup

# === Start Command ===
@dp.message(CommandStart())
async def send_welcome(message: types.Message):
    await db.get_user(message.from_user.id)
    
    missing = await get_missing_channels(message.from_user.id)
    if missing:
        markup = await fsub_markup(missing)
        await message.answer("<b>Join Channel To Use This Bot</b>", reply_markup=markup, parse_mode=ParseMode.HTML)
        return

    text = ("<b>Send Me TeraBox Links</b>\n\n"
            "/videos use This For Videos\n"
            "/videos use This For Videos\n\n"
            "<b>For TeraBox Links ❤️</b>")
    await message.answer(text, parse_mode=ParseMode.HTML)

# === Joined Callback ===
@dp.callback_query(F.data == "verify_join")
async def verify_join_callback(call: types.CallbackQuery):
    missing = await get_missing_channels(call.from_user.id)
    if not missing:
        text = ("<b>Send Me TeraBox Links</b>\n\n"
                "/videos use This For Videos\n"
                "/videos use This For Videos\n\n"
                "<b>For TeraBox Links ❤️</b>")
        await call.message.edit_text(text, parse_mode=ParseMode.HTML)
        await call.answer("You have successfully joined!", show_alert=False)
    else:
        await call.answer("You haven't joined all channels yet!", show_alert=True)

# === 🔥 Admin Force Sub Control Commands ===
@dp.message(Command("addsub"))
async def add_fsub_cmd(message: types.Message):
    if not await db.get_admin_role(message.from_user.id): return
    try:
        args = message.text.split()
        channel_id = args[1] # e.g. @MyChannel
        channel_url = args[2] # e.g. https://t.me/MyChannel
        await db.add_fsub(channel_id, channel_url)
        await message.answer(f"✅ চ্যানেল <b>{channel_id}</b> সফলভাবে ফোরস সাবস্ক্রাইবে অ্যাড করা হয়েছে!", parse_mode=ParseMode.HTML)
    except:
        await message.answer("⚠️ সঠিক নিয়ম: `/addsub @ChannelUsername https://t.me/ChannelLink`", parse_mode=ParseMode.Markdown)

@dp.message(Command("delsub"))
async def del_fsub_cmd(message: types.Message):
    if not await db.get_admin_role(message.from_user.id): return
    try:
        channel_id = message.text.split()[1]
        await db.remove_fsub(channel_id)
        await message.answer(f"🗑️ চ্যানেল <b>{channel_id}</b> ডাটাবেস থেকে মুছে ফেলা হয়েছে!", parse_mode=ParseMode.HTML)
    except:
        await message.answer("⚠️ সঠিক নিয়ম: `/delsub @ChannelUsername`", parse_mode=ParseMode.Markdown)

@dp.message(Command("channels"))
async def list_fsub_cmd(message: types.Message):
    if not await db.get_admin_role(message.from_user.id): return
    channels = await db.get_all_fsubs()
    if not channels:
        await message.answer("ℹ️ কোনো ফোরস সাবস্ক্রাইব চ্যানেল অ্যাড করা নেই।")
        return
    text = "<b>লিংক করা চ্যানেলসমূহ:</b>\n\n"
    for ch in channels: text += f"🔹 {ch['channel_id']} - {ch['channel_url']}\n"
    await message.answer(text, parse_mode=ParseMode.HTML)

# === Handle Terabox Links ===
@dp.message(F.text.contains("terabox"))
async def handle_link(message: types.Message):
    missing = await get_missing_channels(message.from_user.id)
    if missing:
        markup = await fsub_markup(missing)
        await message.answer("<b>Join Channel To Use This Bot</b>", reply_markup=markup, parse_mode=ParseMode.HTML)
        return

    msg = await message.answer("⏳ Wait 2-4 Seconds.")
    link, size, title = await api.get_terabox_direct_link(message.text)
    
    if not link:
        await msg.edit_text("❌ লিংকটি কাজ করছে না অথবা প্রাইভেট করা আছে।")
        return
    
    if size and size <= 50 * 1024 * 1024:
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
            await msg.edit_text("❌ ভিডিও পাঠাতে সমস্যা হয়েছে।")
            if os.path.exists(file_path): os.remove(file_path)
    else:
        player_url = f"{config.WEBAPP_URL}/player.html?link={link}&title={title}"
        markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="▶️ Watch & Download", web_app=WebAppInfo(url=player_url))]])
        await msg.edit_text(f"📁 <b>{title}</b>\n\n⚠️ File is too large for Telegram. Watch or download below:", reply_markup=markup, parse_mode=ParseMode.HTML)

# === Web Server ===
async def web_server():
    app = web.Application()
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 8080))).start()

async def main():
    await db.init_db()
    await asyncio.gather(dp.start_polling(bot), web_server())

if __name__ == "__main__":
    asyncio.run(main())
