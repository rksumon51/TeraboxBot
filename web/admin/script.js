// 🔴 আপনার Railway-এর ডোমেইন লিংকটি এখানে দিন (অবশ্যই https:// সহ এবং শেষে / ছাড়া):
const API_BASE = "worker-production-0420.up.railway.app"; 

const tg = window.Telegram.WebApp; 
tg.expand();

// === Sidebar & Tab Logic ===
const sidebar = document.querySelector('.sidebar');
const menuToggle = document.getElementById('menuToggle');

menuToggle.addEventListener('click', (e) => {
    e.stopPropagation();
    sidebar.classList.toggle('active');
});

// স্ক্রিনের খালি জায়গায় ক্লিক করলে সাইডবার বন্ধ হবে
document.addEventListener('click', (e) => {
    if (window.innerWidth <= 768 && sidebar.classList.contains('active')) {
        if (!sidebar.contains(e.target) && !menuToggle.contains(e.target)) {
            sidebar.classList.remove('active');
        }
    }
});

// মেনু বাটন দিয়ে পেজ (Tab) চেঞ্জ করার লজিক
function switchTab(tabName) {
    // সব ট্যাব হাইড করো
    document.getElementById('view-home').style.display = 'none';
    document.getElementById('view-forcesub').style.display = 'none';
    document.getElementById('view-broadcast').style.display = 'none';
    
    // সব মেনু থেকে active ক্লাস সরাও
    document.getElementById('nav-home').classList.remove('active');
    document.getElementById('nav-forcesub').classList.remove('active');
    document.getElementById('nav-broadcast').classList.remove('active');
    
    // শুধু সিলেক্ট করা ট্যাব শো করো
    document.getElementById(`view-${tabName}`).style.display = 'block';
    document.getElementById(`nav-${tabName}`).classList.add('active');
    
    // মোবাইলে ক্লিক করার পর সাইডবার নিজে থেকেই বন্ধ হয়ে যাবে
    if (window.innerWidth <= 768) {
        sidebar.classList.remove('active');
    }
}

// === Data Loading & APIs ===
async function loadData() {
    if (API_BASE.includes("এখানে-আপনার-রেলওয়ের-লিংক-দিন")) {
        document.getElementById('userCount').innerText = "Link Missing!";
        return tg.showAlert("⚠️ দয়া করে script.js ফাইলে আপনার Railway লিংকটি বসান!");
    }
    
    try {
        const res = await fetch(`${API_BASE}/api/stats`);
        const data = await res.json();
        
        document.getElementById('userCount').innerText = data.users.toLocaleString();
        document.getElementById('activeUserCount').innerText = Math.floor(data.users * 0.85).toLocaleString();
        document.getElementById('subCount').innerText = data.subs.length;
        document.getElementById('broadcastBadge').innerText = `Total Users: ${data.users.toLocaleString()}`;
        
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
        document.getElementById('userCount').innerText = "API Error";
        tg.showAlert("⚠️ Railway সার্ভারের সাথে কানেক্ট করা যাচ্ছে না। লিংকটি চেক করুন।");
    }
}

async function addSub() {
    const id = document.getElementById('chId').value;
    const url = document.getElementById('chUrl').value;
    if(!id || !url) return tg.showAlert("Please fill both Channel ID and Link fields!");
    
    tg.MainButton.text = "Saving Channel..."; tg.MainButton.show();
    await fetch(`${API_BASE}/api/add_sub`, {
        method: 'POST', body: JSON.stringify({channel_id: id, channel_url: url}), headers: {'Content-Type': 'application/json'}
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
                method: 'POST', body: JSON.stringify({channel_id: id}), headers: {'Content-Type': 'application/json'}
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
            tg.MainButton.text = "Sending Broadcast..."; tg.MainButton.show();
            await fetch(`${API_BASE}/api/broadcast`, {
                method: 'POST', body: JSON.stringify({message: msg}), headers: {'Content-Type': 'application/json'}
            });
            tg.showAlert("✅ Broadcast Sent Successfully!");
            tg.MainButton.hide();
            document.getElementById('bMsg').value = "";
        }
    });
}

// পেজ ওপেন হওয়ার সাথে সাথে ডাটা লোড করবে
loadData();
