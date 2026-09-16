import aiohttp
import re
import random
import database as db

# 🔴 IP Spoofing (প্রতিবার নতুন আইপি জেনারেট করবে)
def get_random_ip():
    return f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"

async def get_terabox_direct_link(text, request_type="download"):
    try:
        match = re.search(r'(https?://[^\s]+(?:terabox|tera)[^\s]+)', text)
        if not match: return None, None, None
        terabox_url = match.group(1)
        
        settings = await db.get_settings()
        user_apis = settings.get(f"{request_type}_apis", [])
        
        # 🔥 Best Working APIs
        hidden_apis = [
            "https://terabox.hnn.workers.dev/api/get-info?shorturl=",
            "https://ytshorts.savetube.me/api/v1/terabox-downloader",
            "https://teraboxvideodownloader.nepcoderdevs.workers.dev/?url=",
            "https://1024teradl.com/api/proxy"
        ]
        all_apis = user_apis + hidden_apis
        
        timeout = aiohttp.ClientTimeout(total=10)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            for api_url in all_apis:
                try:
                    print(f"🔄 Trying (aiohttp spoofing): {api_url}")
                    
                    # 🔴 MAGIC HEADERS: Cloudflare ভাববে রিয়েল মানুষ আসছে
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
                        "Accept": "application/json",
                        "X-Forwarded-For": get_random_ip(), # ভুয়া আইপি
                        "Referer": "https://www.google.com/"
                    }
                    
                    # 1. POST API
                    if "proxy" in api_url or "savetube" in api_url:
                        clean_api = api_url.split('?url=')[0]
                        domain = clean_api.split('/api')[0]
                        headers["Origin"] = domain
                        headers["Referer"] = f"{domain}/"
                        
                        async with session.post(clean_api, json={"url": terabox_url}, headers=headers) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                link = data.get('dlink') or data.get('direct_link') or data.get('url')
                                if not link and "response" in data and len(data["response"]) > 0:
                                    link = data["response"][0].get("resolutions", {}).get("Fast Download", data["response"][0].get("link"))
                                if link: 
                                    print(f"✅ SUCCESS (POST): {clean_api}")
                                    return link, 0, "Video.mp4"
                            else:
                                print(f"❌ POST Blocked: Status {resp.status}")
                    
                    # 2. GET API
                    else:
                        req_url = f"{api_url}{terabox_url}" if api_url.endswith('=') else f"{api_url}?url={terabox_url}"
                        if "shorturl=" in api_url:
                            short_match = re.search(r'/s/([a-zA-Z0-9_-]+)', terabox_url)
                            if short_match: req_url = f"{api_url}{short_match.group(1)}"
                            else: continue
                            
                        async with session.get(req_url, headers=headers) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                if "list" in data and len(data["list"]) > 0:
                                    video = data["list"][0]
                                    print(f"✅ SUCCESS (Worker): {api_url}")
                                    return video.get("dlink"), int(video.get("size", 0)), video.get("filename", "Video.mp4")
                                
                                link = data.get('dlink') or data.get('direct_link') or data.get('url')
                                if link: 
                                    print(f"✅ SUCCESS (GET): {api_url}")
                                    return link, 0, "Video.mp4"
                            else:
                                print(f"❌ GET Blocked: Status {resp.status}")
                
                except Exception as e:
                    print(f"⚠️ Failed {api_url}: {str(e)[:30]}")
                    continue 
                    
    except Exception as e:
        print(f"🚨 Main Error: {e}")
        
    return None, None, None
