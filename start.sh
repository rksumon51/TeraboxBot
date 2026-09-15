#!/bin/bash
echo "🟢 라이ব্রেরি চেক করা হচ্ছে..."
pip install -r requirements.txt -q
echo "🚀 Terabox Bot এবং Web Server চালু হচ্ছে..."
python bot.py
