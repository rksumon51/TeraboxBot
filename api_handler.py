import aiohttp
import re

async def get_terabox_direct_link(text):
    try:
        # মেসেজ থেকে লিংক বের করা
        match = re.search(r'(https?://[^\s]+(?:terabox|tera)[^\s]+)', text)
        if not match:
            return None, None, None
        
        url = match.group(1)
        
        # ⏳ ৮ সেকেন্ডের টাইমআউট, যাতে বট হ্যাং হয়ে না থাকে
        timeout = aiohttp.ClientTimeout(total=8)
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        }
        
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            
            # 🔥 API 1: Website Video Downloader (Very Fast)
            try:
                api_1 = "https://ytshorts.savetube.me/api/v1/terabox-downloader"
                async with session.post(api_1, json={"url": url}) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if "response" in data and len(data["response"]) > 0:
                            video = data["response"][0]
                            # ডিরেক্ট লিংক এবং টাইটেল
                            link = video.get("resolutions", {}).get("Fast Download", video.get("link"))
                            title = video.get("title", "Terabox_Video.mp4")
                            
                            # সাইজ (MB/GB) ক্যালকুলেট করে বাইটে কনভার্ট করা
                            size_str = str(video.get("size", "0 MB"))
                            size_bytes = 0
                            if "MB" in size_str: size_bytes = float(size_str.replace("MB", "").strip()) * 1024 * 1024
                            elif "GB" in size_str: size_bytes = float(size_str.replace("GB", "").strip()) * 1024 * 1024 * 1024
                            
                            if link: return link, size_bytes, title
            except Exception as e:
                print(f"API 1 Failed: {e}")

            # ♻️ API 2: Fallback Downloader API (যদি প্রথমটি কাজ না করে)
            try:
                # লিংক থেকে shorturl আইডি বের করা (যেমন: 1CIWi7nOPloW...)
                shorturl_match = re.search(r'/s/([a-zA-Z0-9_-]+)', url)
                if shorturl_match:
                    shorturl = shorturl_match.group(1)
                    api_2 = f"https://terabox-dl.qtcloud.workers.dev/api/get-info?shorturl={shorturl}"
                    
                    async with session.get(api_2) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if "list" in data and len(data["list"]) > 0:
                                video = data["list"][0]
                                link = video.get("dlink")
                                title = video.get("filename", "Terabox_Video.mp4")
                                size_bytes = int(video.get("size", 0))
                                
                                if link: return link, size_bytes, title
            except Exception as e:
                print(f"API 2 Failed: {e}")

    except Exception as e:
        print(f"Main Terabox Error: {e}")
        
    return None, None, None
