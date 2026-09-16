import aiohttp
import re
import database as db

# 🔴 Smart JSON Parser (যেকোনো ফরম্যাট থেকে লিংক খুঁজবে)
def find_data(data, target_keys):
    if isinstance(data, dict):
        for k, v in data.items():
            # 'url' বাদ দেওয়া হয়েছে কারণ অনেক সময় রিকোয়েস্টের url ব্যাক আসে
            if k.lower() in target_keys and isinstance(v, str) and v.startswith('http'):
                return v
            res = find_data(v, target_keys)
            if res is not None: return res
    elif isinstance(data, list):
        for item in data:
            res = find_data(item, target_keys)
            if res is not None: return res
    return None

async def get_terabox_direct_link(text, request_type="download"):
    try:
        match = re.search(r'(https?://[^\s]+(?:terabox|tera)[^\s]+)', text)
        if not match: return None, None, None
        terabox_url = match.group(1)
        
        settings = await db.get_settings()
        user_apis = settings.get(f"{request_type}_apis", [])
        
        # 🔥 ৩টি সুপারফাস্ট হিডেন API (বটের লাইফসেভার)
        hidden_apis = [
            "https://ytshorts.savetube.me/api/v1/terabox-downloader",
            "https://terabox-dl.qtcloud.workers.dev/api/get-info?shorturl=",
            "https://teraboxvideodownloader.nepcoderdevs.workers.dev/?url="
        ]
        
        # প্যানেলের API কাজ না করলে অটোমেটিক হিডেন API তে যাবে
        all_apis = user_apis + hidden_apis
        timeout = aiohttp.ClientTimeout(total=5) # ৫ সেকেন্ডের বেশি আটকে থাকবে না
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64 AppleWebKit/537.36)"}
        
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            for api_url in all_apis:
                try:
                    # 1. Savetube বা POST API লজিক (আপনার বের করা API এর মতো)
                    if "savetube" in api_url or "proxy" in api_url:
                        clean_api = api_url.split('?url=')[0]
                        async with session.post(clean_api, json={"url": terabox_url}) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                link = find_data(data, ['dlink', 'link', 'direct_link', 'fast download'])
                                if link: return link, 15*1024*1024, "Terabox_Video.mp4"
                    
                    # 2. QTCloud ShortURL লজিক (সবচেয়ে ফাস্ট)
                    elif "qtcloud" in api_url:
                        short_match = re.search(r'/s/([a-zA-Z0-9_-]+)', terabox_url)
                        if short_match:
                            req_url = f"{api_url}{short_match.group(1)}"
                            async with session.get(req_url) as resp:
                                if resp.status == 200:
                                    data = await resp.json()
                                    if "list" in data and len(data["list"]) > 0:
                                        video = data["list"][0]
                                        if video.get("dlink"):
                                            return video.get("dlink"), int(video.get("size", 15*1024*1024)), video.get("filename", "Video.mp4")

                    # 3. সাধারণ GET API লজিক (প্যানেল থেকে বসানো)
                    else:
                        req_url = f"{api_url}{terabox_url}" if api_url.endswith('=') else f"{api_url}?url={terabox_url}"
                        async with session.get(req_url) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                
                                if "response" in data and len(data["response"]) > 0:
                                    video = data["response"][0]
                                    link = video.get("resolutions", {}).get("Fast Download", video.get("link"))
                                    if link: return link, 15*1024*1024, video.get("title", "Video.mp4")
                                    
                                link = find_data(data, ['dlink', 'link', 'direct_link'])
                                if link: return link, 15*1024*1024, "Video.mp4"
                except Exception as e:
                    print(f"API Blocked or Failed: {api_url}")
                    continue # একটি কাজ না করলে বা ব্লক হলে অটোমেটিক স্কিপ করে পরেরটায় যাবে

    except Exception as e:
        print(f"Main Terabox Error: {e}")
        
    return None, None, None
