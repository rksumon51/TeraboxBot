import aiohttp
import re
import database as db

# 🔴 Smart JSON Parser (যেকোনো API থেকে লিংক খুঁজে বের করবে)
def extract_link(data):
    if isinstance(data, dict):
        for k, v in data.items():
            if k.lower() in ['dlink', 'link', 'url', 'direct_link', 'download_link', 'fast download'] and isinstance(v, str) and v.startswith('http'):
                return v
            res = extract_link(v)
            if res: return res
    elif isinstance(data, list):
        for item in data:
            res = extract_link(item)
            if res: return res
    return None

async def get_terabox_direct_link(text, request_type="download"):
    try:
        match = re.search(r'(https?://[^\s]+(?:terabox|tera)[^\s]+)', text)
        if not match: return None, None, None
        
        terabox_url = match.group(1)
        settings = await db.get_settings()
        
        # প্যানেল থেকে ডাউনলোড বা স্ট্রিমের API গুলো আনা
        apis = settings.get(f"{request_type}_apis", [])
        if not apis:
            # ফলব্যাক ডিফল্ট API
            apis = ["https://teraboxvideodownloader.nepcoderdevs.workers.dev/?url="]
            
        timeout = aiohttp.ClientTimeout(total=8)
        headers = {"User-Agent": "Mozilla/5.0"}
        
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            for api_base in apis:
                try:
                    # যদি API এর শেষে ?url= থাকে, তবে সরাসরি লিংক বসবে
                    req_url = f"{api_base}{terabox_url}" if api_base.endswith('=') else f"{api_base}?url={terabox_url}"
                    
                    async with session.get(req_url) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            direct_link = extract_link(data)
                            
                            if direct_link:
                                # টাইটেল এবং সাইজ খোঁজার চেষ্টা
                                title = "Terabox_Video.mp4"
                                size_bytes = 0
                                
                                # সাধারনভাবে সাইজ বের করার লজিক
                                str_data = str(data)
                                if "MB" in str_data: size_bytes = 15 * 1024 * 1024 # অনুমানিক
                                
                                return direct_link, size_bytes, title
                except Exception as e:
                    print(f"API Failed: {api_base} - {e}")
                    continue # একটি কাজ না করলে পরের API তে যাবে (আনলিমিটেড ফলব্যাক)

    except Exception as e:
        print(f"Main Terabox Error: {e}")
        
    return None, None, None
