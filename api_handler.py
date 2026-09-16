import re
import database as db
from curl_cffi.requests import AsyncSession

async def get_terabox_direct_link(text, request_type="download"):
    try:
        match = re.search(r'(https?://[^\s]+(?:terabox|tera)[^\s]+)', text)
        if not match: return None, None, None
        terabox_url = match.group(1)
        
        settings = await db.get_settings()
        user_apis = settings.get(f"{request_type}_apis", [])
        
        # 🔥 ৫টি ফ্রেশ API যেগুলো Railway IP তে কাজ করে
        hidden_apis = [
            "https://terabox.hnn.workers.dev/api/get-info?shorturl=",
            "https://teraboxvideodownloader.nepcoderdevs.workers.dev/?url=",
            "https://tera.dapunthea.workers.dev/api/get-info?shorturl=",
            "https://1024teradl.com/api/proxy",
            "https://ytshorts.savetube.me/api/v1/terabox-downloader"
        ]
        all_apis = user_apis + hidden_apis
        
        # chrome116 ইউজ করা হচ্ছে যাতে লেটেস্ট ব্রাউজার মনে হয়
        async with AsyncSession(impersonate="chrome116", timeout=12) as session:
            for api_url in all_apis:
                try:
                    print(f"🔄 Trying: {api_url}")
                    
                    # 1. POST API (1024teradl, savetube)
                    if "proxy" in api_url or "savetube" in api_url:
                        clean_api = api_url.split('?url=')[0]
                        domain = clean_api.split('/api')[0]
                        
                        # 🔴 MAGIC HEADERS: ওয়েবসাইট ভাববে আপনি ওয়েবসাইটেই আছেন!
                        headers = {
                            "Origin": domain,
                            "Referer": f"{domain}/",
                            "Accept": "application/json"
                        }
                        
                        resp = await session.post(clean_api, json={"url": terabox_url}, headers=headers)
                        
                        if resp.status_code == 200:
                            data = resp.json()
                            link = data.get('dlink') or data.get('direct_link') or data.get('url')
                            if not link and "response" in data and len(data["response"]) > 0:
                                link = data["response"][0].get("resolutions", {}).get("Fast Download", data["response"][0].get("link"))
                            if link: 
                                print(f"✅ SUCCESS (POST): {clean_api}")
                                return link, 0, "Video.mp4"
                    
                    # 2. GET API (Cloudflare Workers)
                    else:
                        req_url = f"{api_url}{terabox_url}" if api_url.endswith('=') else f"{api_url}?url={terabox_url}"
                        
                        # যদি shorturl API হয়, তবে শুধু আইডি বের করে বসাবে
                        if "shorturl=" in api_url:
                            short_match = re.search(r'/s/([a-zA-Z0-9_-]+)', terabox_url)
                            if short_match:
                                req_url = f"{api_url}{short_match.group(1)}"
                            else:
                                continue 
                                
                        resp = await session.get(req_url)
                        
                        if resp.status_code == 200:
                            data = resp.json()
                            
                            # Worker API Format চেক করা
                            if "list" in data and len(data["list"]) > 0:
                                video = data["list"][0]
                                print(f"✅ SUCCESS (Worker): {api_url}")
                                return video.get("dlink"), int(video.get("size", 0)), video.get("filename", "Video.mp4")
                            
                            link = data.get('dlink') or data.get('direct_link') or data.get('url')
                            if not link and "response" in data and len(data["response"]) > 0:
                                link = data["response"][0].get("resolutions", {}).get("Fast Download", data["response"][0].get("link"))
                            if link: 
                                print(f"✅ SUCCESS (GET): {api_url}")
                                return link, 0, "Video.mp4"
                
                except Exception as e:
                    print(f"⚠️ Failed {api_url}: {str(e)[:30]}")
                    continue 
                    
    except Exception as e:
        print(f"🚨 Main Error: {e}")
        
    return None, None, None
