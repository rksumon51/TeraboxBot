#!/bin/bash

cat << 'EOF' > /data/data/com.termux/files/usr/bin/Terabot
#!/bin/bash
cd $HOME/TeraboxBot
clear
echo "==================================="
echo "       🤖 TERABOX BOT MENU         "
echo "==================================="
echo "  [1] ▶️ Start Bot (বট চালু করুন)"
echo "  [2] ⏹️ Stop Bot (বট বন্ধ করুন)"
echo "  [3] 🔄 Update Bot (নতুন আপডেট আনুন)"
echo "  [4] ❌ Exit (বেরিয়ে যান)"
echo "==================================="
read -p "Select option (1/2/3/4): " choice

case $choice in
    1) 
        echo "⏳ বট চালু হচ্ছে..."
        nohup bash start.sh > bot.log 2>&1 & 
        echo $! > bot.pid
        echo "✅ বট ব্যাকগ্রাউন্ডে চালু হয়েছে! (Termux কেটে দিতে পারেন)"
        ;;
    2) 
        if [ -f bot.pid ]; then 
            kill -9 $(cat bot.pid)
            rm bot.pid
            echo "🛑 বট সফলভাবে বন্ধ করা হয়েছে।"
        else 
            echo "⚠️ বট আগে থেকেই বন্ধ আছে।"
        fi
        ;;
    3) 
        echo "🔄 গিটহাব থেকে নতুন আপডেট চেক করা হচ্ছে..."
        git pull origin main
        pip install -r requirements.txt -q
        echo "✅ আপডেট কমপ্লিট! এখন ১ চেপে বট স্টার্ট করতে পারেন।"
        ;;
    4) 
        exit 0 
        ;;
    *) 
        echo "❌ ভুল অপশন!" 
        ;;
esac
EOF

chmod +x /data/data/com.termux/files/usr/bin/Terabot
echo "✅ Setup done! Termux-এ যেকোনো জায়গায় 'Terabot' লিখে এন্টার দিন।"
