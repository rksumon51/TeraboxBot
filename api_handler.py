import aiohttp
import re
import database as db

async def get_terabox_direct_link(text, request_type="download"):
    try:
        match = re.search(r'(https?://[^\s]+(?:terabox|tera)[^\s]+)', text)
        if not match: return None, None, None
        terabox_url = match.group(1)
        
        settings = await db.get_settings()
        user_apis = settings.get(f"{request_type}_apis", [])
        
        # 🔥 5 Bulletproof Worker APIs (Railway IP ব্লক হবে না)
        hidden_apis = [
            "https://ytshorts.savetube.me/api/v1/terabox-downloader",
            "https://teraboxvideodownloader.nepcoderdevs.workers.dev/?url=",
            "https://terabox-dl.qtcloud.workers.dev/api/get-info?shorturl=",
            "https://dl.imouto.workers.dev/api/get-info?shorturl="
        ]
        all_apis = user_apis + hidden_apis
        
        timeout = aiohttp.ClientTimeout(total=10)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        }
        
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            for api_url in all_apis:
                try:
                    print(f"🔄 Trying API: {api_url}")
                    
                    # 1. POST APIs
                    if "proxy" in api_url or "savetube" in api_url:
                        clean_api = api_url.split('?url=')[0]
                        async with session.post(clean_api, json={"url": terabox_url}) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                link = data.get('dlink') or data.get('direct_link') or data.get('url')
                                if not link and "response" in data and len(data["response"]) > 0:
                                    link = data["response"][0].get("resolutions", {}).get("Fast Download", data["response"][0].get("link"))
                                if link: 
                                    print(f"✅ Success with POST API: {clean_api}")
                                    return link, 0, "Video.mp4"
                            else:
                                print(f"❌ POST Failed! Status: {resp.status} (API Blocked)")
                    
                    # 2. ShortURL GET APIs (Cloudflare Workers)
                    elif "qtcloud" in api_url or "imouto" in api_url:
                        short_match = re.search(r'/s/([a-zA-Z0-9_-]+)', terabox_url)
                        if short_match:
                            req_url = f"{api_url}{short_match.group(1)}"
                            async with session.get(req_url) as resp:
                                if resp.status == 200:
                                    data = await resp.json()
                                    if "list" in data and len(data["list"]) > 0:
                                        video = data["list"][0]
                                        print(f"✅ Success with ShortURL API: {api_url}")
                                        return video.get("dlink"), int(video.get("size", 0)), video.get("filename", "Video.mp4")
                                else:
                                    print(f"❌ ShortURL Failed! Status: {resp.status}")
                    
                    # 3. Normal GET APIs
                    else:
                        req_url = f"{api_url}{terabox_url}" if api_url.endswith('=') else f"{api_url}?url={terabox_url}"
                        async with session.get(req_url) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                link = data.get('dlink') or data.get('direct_link') or data.get('url')
                                if not link and "response" in data and len(data["response"]) > 0:
                                    link = data["response"][0].get("resolutions", {}).get("Fast Download", data["response"][0].get("link"))
                                if link: 
                                    print(f"✅ Success with GET API: {api_url}")
                                    return link, 0, "Video.mp4"
                            else:
                                print(f"❌ GET Failed! Status: {resp.status}")
                
                except Exception as e:
                    print(f"⚠️ Error with API {api_url}: {e}")
                    continue 
                    
    except Exception as e:
        print(f"🚨 Critical Error: {e}")
        
    return None, None, None
