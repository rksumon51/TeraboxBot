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
        
        # 🔥 আপনার বের করা API সহ সেরা API গুলো (এখন আর ব্লক হবে না)
        hidden_apis = [
            "https://1024teradl.com/api/proxy",
            "https://teraboxvideodownloader.nepcoderdevs.workers.dev/?url="
        ]
        all_apis = user_apis + hidden_apis
        
        # 🚀 MAGIC: পাইথনকে Google Chrome (chrome110) সাজিয়ে রিকোয়েস্ট পাঠানো হচ্ছে
        async with AsyncSession(impersonate="chrome110", timeout=15) as session:
            for api_url in all_apis:
                try:
                    print(f"🔄 Browser Spoofing Try: {api_url}")
                    
                    # 1. POST API (1024teradl Proxy)
                    if "proxy" in api_url or "savetube" in api_url:
                        clean_api = api_url.split('?url=')[0]
                        resp = await session.post(clean_api, json={"url": terabox_url})
                        
                        if resp.status_code == 200:
                            data = resp.json()
                            link = data.get('dlink') or data.get('direct_link') or data.get('url')
                            if link: 
                                print(f"✅ HACK SUCCESS! CF Bypassed: {clean_api}")
                                return link, 0, "Video.mp4"
                        else:
                            print(f"❌ POST Failed! Status: {resp.status_code}")
                    
                    # 2. GET APIs
                    else:
                        req_url = f"{api_url}{terabox_url}" if api_url.endswith('=') else f"{api_url}?url={terabox_url}"
                        resp = await session.get(req_url)
                        
                        if resp.status_code == 200:
                            data = resp.json()
                            link = data.get('dlink') or data.get('direct_link') or data.get('url')
                            if not link and "response" in data and len(data["response"]) > 0:
                                link = data["response"][0].get("resolutions", {}).get("Fast Download", data["response"][0].get("link"))
                            if link: 
                                print(f"✅ HACK SUCCESS! CF Bypassed: {api_url}")
                                return link, 0, "Video.mp4"
                        else:
                            print(f"❌ GET Failed! Status: {resp.status_code}")
                
                except Exception as e:
                    print(f"⚠️ Error with API {api_url}: {e}")
                    continue 
                    
    except Exception as e:
        print(f"🚨 Critical Error: {e}")
        
    return None, None, None
