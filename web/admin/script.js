const tg = window.Telegram.WebApp; 
tg.expand();

const sidebar = document.querySelector('.sidebar');
const menuToggle = document.getElementById('menuToggle');

// Sidebar toggle for mobile
menuToggle.addEventListener('click', (e) => {
    e.stopPropagation(); // বাটনে ক্লিক করলে যেন সাথে সাথে বন্ধ না হয়ে যায়
    sidebar.classList.toggle('active');
});

// খালি জায়গায় (Outside) ক্লিক করলে সাইডবার বন্ধ করার লজিক
document.addEventListener('click', (e) => {
    // মোবাইল স্ক্রিন সাইজ (768px এর নিচে) হলে এবং সাইডবার ওপেন থাকলে
    if (window.innerWidth <= 768 && sidebar.classList.contains('active')) {
        // যদি ক্লিকটা সাইডবারের ভেতরে বা মেনু বাটনে না হয়
        if (!sidebar.contains(e.target) && !menuToggle.contains(e.target)) {
            sidebar.classList.remove('active');
        }
    }
});

const params = new URLSearchParams(window.location.search);
const API_BASE = params.get('api') || "";

async function loadData() {
    if(!API_BASE) return;
    try {
        const res = await fetch(`${API_BASE}/api/stats`);
        const data = await res.json();
        
        // Update Stats
        document.getElementById('userCount').innerText = data.users.toLocaleString();
        document.getElementById('activeUserCount').innerText = Math.floor(data.users * 0.85).toLocaleString(); // Example active logic
        document.getElementById('subCount').innerText = data.subs.length;
        document.getElementById('broadcastBadge').innerText = `Total Users: ${data.users.toLocaleString()}`;
        
        // Update Channels List
        const list = document.getElementById('subList');
        list.innerHTML = "";
        if(data.subs.length === 0) {
            list.innerHTML = `<li style="justify-content:center; color:#94a3b8; border-left:none;">No channels added yet</li>`;
        } else {
            data.subs.forEach(sub => {
                list.innerHTML += `
                    <li>
                        <span><i class="fa-brands fa-telegram" style="color:#2563eb; margin-right:8px;"></i> ${sub.id}</span>
                        <button class="delete-btn" onclick="delSub('${sub.id}')"><i class="fa-solid fa-trash"></i></button>
                    </li>`;
            });
        }
    } catch (e) {
        document.getElementById('userCount').innerText = "Error";
    }
}

async function addSub() {
    const id = document.getElementById('chId').value;
    const url = document.getElementById('chUrl').value;
    if(!id || !url) return tg.showAlert("Please fill both Channel ID and Link fields!");
    
    tg.MainButton.text = "Saving Channel..."; 
    tg.MainButton.show();
    
    await fetch(`${API_BASE}/api/add_sub`, {
        method: 'POST', 
        body: JSON.stringify({channel_id: id, channel_url: url}), 
        headers: {'Content-Type': 'application/json'}
    });
    
    tg.MainButton.hide();
    document.getElementById('chId').value = "";
    document.getElementById('chUrl').value = "";
    loadData();
    tg.showAlert("✅ Channel added successfully!");
}

async function delSub(id) {
    tg.showConfirm(`Are you sure you want to remove ${id}?`, async function(confirmed) {
        if(confirmed) {
            await fetch(`${API_BASE}/api/del_sub`, {
                method: 'POST', 
                body: JSON.stringify({channel_id: id}), 
                headers: {'Content-Type': 'application/json'}
            });
            loadData();
        }
    });
}

async function sendBroadcast() {
    const msg = document.getElementById('bMsg').value;
    if(!msg) return tg.showAlert("Broadcast message cannot be empty!");
    
    tg.showConfirm("Send this message to ALL users?", async function(confirmed) {
        if(confirmed) {
            tg.MainButton.text = "Sending Broadcast..."; 
            tg.MainButton.show();
            
            await fetch(`${API_BASE}/api/broadcast`, {
                method: 'POST', 
                body: JSON.stringify({message: msg}), 
                headers: {'Content-Type': 'application/json'}
            });
            
            tg.showAlert("✅ Broadcast Sent Successfully!");
            tg.MainButton.hide();
            document.getElementById('bMsg').value = "";
        }
    });
}

// Initial Load
loadData();
