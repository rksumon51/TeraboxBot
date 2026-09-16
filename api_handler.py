import re
import asyncio
import cloudscraper
import database as db

# 🔴 Cloudscraper: Cloudflare Bypass এর মাস্টার! 
def fetch_link_sync(terabox_url, apis):
    # রিয়েল ব্রাউজার সাজানোর জন্য cloudscraper
    scraper = cloudscraper.create_scraper(browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True
    })
    
    for api_url in apis:
        try:
            print(f"🔄 Cloudscraper Trying: {api_url}")
            
            # 1. POST APIs (1024teradl, savetube)
            if "proxy" in api_url or "savetube" in api_url:
                clean_api = api_url.split('?url=')[0]
                domain = clean_api.split('/api')[0]
                
                headers = {
                    "Origin": domain,
                    "Referer": f"{domain}/",
                    "Accept": "application/json"
                }
                
                resp = scraper.post(clean_api, json={"url": terabox_url}, headers=headers, timeout=15)
                
                if resp.status_code == 200:
                    data = resp.json()
                    link = data.get('dlink') or data.get('direct_link') or data.get('url')
                    if not link and "response" in data and len(data["response"]) > 0:
                        link = data["response"][0].get("resolutions", {}).get("Fast Download", data["response"][0].get("link"))
                    if link: 
                        print(f"✅ HACK SUCCESS (POST): {clean_api}")
                        return link, 0, "Video.mp4"
                else:
                    print(f"❌ CF Blocked POST: {resp.status_code}")
            
            # 2. GET APIs
            else:
                req_url = f"{api_url}{terabox_url}" if api_url.endswith('=') else f"{api_url}?url={terabox_url}"
                if "shorturl=" in api_url:
                    match = re.search(r'/s/([a-zA-Z0-9_-]+)', terabox_url)
                    if match: req_url = f"{api_url}{match.group(1)}"
                    else: continue
                
                resp = scraper.get(req_url, timeout=15)
                
                if resp.status_code == 200:
                    data = resp.json()
                    if "list" in data and len(data["list"]) > 0:
                        video = data["list"][0]
                        print(f"✅ HACK SUCCESS (Worker): {api_url}")
                        return video.get("dlink"), int(video.get("size", 0)), video.get("filename", "Video.mp4")
                    
                    link = data.get('dlink') or data.get('direct_link') or data.get('url')
                    if link: 
                        print(f"✅ HACK SUCCESS (GET): {api_url}")
                        return link, 0, "Video.mp4"
                else:
                    print(f"❌ CF Blocked GET: {resp.status_code}")
                    
        except Exception as e:
            print(f"⚠️ Error {api_url}: {str(e)[:30]}")
            continue
            
    return None, None, None

async def get_terabox_direct_link(text, request_type="download"):
    try:
        match = re.search(r'(https?://[^\s]+(?:terabox|tera)[^\s]+)', text)
        if not match: return None, None, None
        terabox_url = match.group(1)
        
        settings = await db.get_settings()
        user_apis = settings.get(f"{request_type}_apis", [])
        
        # 🔥 Best Working APIs
        hidden_apis = [
            "https://1024teradl.com/api/proxy",
            "https://terabox.hnn.workers.dev/api/get-info?shorturl=",
            "https://teraboxvideodownloader.nepcoderdevs.workers.dev/?url="
        ]
        all_apis = user_apis + hidden_apis
        
        # 🚀 Asyncio thread-এ synchronous cloudscraper রান করানো হচ্ছে
        link, size, title = await asyncio.to_thread(fetch_link_sync, terabox_url, all_apis)
        return link, size, title
        
    except Exception as e:
        print(f"🚨 Main Error: {e}")
        
    return None, None, None
