import aiohttp
import re
import database as db

# 🔴 Smart JSON Parser (API থেকে ডাটা খুঁজে বের করার এআই)
def find_data(data, target_keys):
    if isinstance(data, dict):
        for k, v in data.items():
            if k.lower() in target_keys and v:
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
        
        apis = settings.get(f"{request_type}_apis", [])
        if not apis:
            apis = ["https://teraboxvideodownloader.nepcoderdevs.workers.dev/?url="]
            
        timeout = aiohttp.ClientTimeout(total=10)
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            for api_base in apis:
                try:
                    # 🚀 ১. প্রথমে POST রিকোয়েস্ট ট্রাই করবে (আপনার স্ক্রিনশটের মতো)
                    post_data = {"url": terabox_url}
                    clean_api = api_base.split('?url=')[0] # লিংকের শেষে ?url= থাকলে মুছে দিবে
                    
                    async with session.post(clean_api, json=post_data) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            direct_link = find_data(data, ['dlink', 'link', 'url', 'direct_link', 'download_link'])
                            
                            if direct_link and str(direct_link).startswith('http'):
                                # টাইটেল এবং সাইজ অটোমেটিক বের করা
                                title = find_data(data, ['title', 'filename', 'name']) or "Terabox_Video.mp4"
                                size_bytes = find_data(data, ['total_size_bytes', 'sizebytes', 'size']) or 0
                                
                                # যদি সাইজ MB/GB তে থাকে
                                if isinstance(size_bytes, str):
                                    if "MB" in size_bytes: size_bytes = float(size_bytes.replace("MB", "").strip()) * 1024 * 1024
                                    elif "GB" in size_bytes: size_bytes = float(size_bytes.replace("GB", "").strip()) * 1024 * 1024 * 1024
                                    else: size_bytes = 0
                                    
                                return direct_link, int(size_bytes), title
                                
                    # 🚀 ২. POST কাজ না করলে GET রিকোয়েস্ট ট্রাই করবে
                    req_url = f"{api_base}{terabox_url}" if api_base.endswith('=') else f"{api_base}?url={terabox_url}"
                    async with session.get(req_url) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            direct_link = find_data(data, ['dlink', 'link', 'url', 'direct_link'])
                            
                            if direct_link and str(direct_link).startswith('http'):
                                title = find_data(data, ['title', 'filename']) or "Terabox_Video.mp4"
                                size = find_data(data, ['total_size_bytes', 'size']) or 0
                                return direct_link, int(size), title
                except Exception as e:
                    print(f"API Failed: {api_base} - {e}")
                    continue

    except Exception as e:
        print(f"Main Terabox Error: {e}")
        
    return None, None, None
