const tg = window.Telegram.WebApp; 
tg.expand();

const params = new URLSearchParams(window.location.search);
const API_BASE = params.get('api') || "";

async function loadData() {
    if(!API_BASE) return;
    try {
        const res = await fetch(`${API_BASE}/api/stats`);
        const data = await res.json();
        
        document.getElementById('userCount').innerText = data.users;
        
        const list = document.getElementById('subList');
        list.innerHTML = "";
        data.subs.forEach(sub => {
            list.innerHTML += `<li>${sub.id} <button class="delete-btn" onclick="delSub('${sub.id}')">🗑️</button></li>`;
        });
    } catch (e) {
        document.getElementById('userCount').innerText = "Connection Error";
    }
}

async function addAdmin() {
    const id = document.getElementById('adminId').value;
    const role = document.getElementById('adminRole').value;
    if(!id) return alert("Please enter User ID!");
    
    tg.MainButton.text = "Adding Admin..."; tg.MainButton.show();
    const res = await fetch(`${API_BASE}/api/add_admin`, {
        method: 'POST', body: JSON.stringify({user_id: id, role: role}), headers: {'Content-Type': 'application/json'}
    });
    const data = await res.json();
    tg.MainButton.hide();
    
    if(data.status === 'ok') alert("✅ Admin added successfully!");
    else alert("⚠️ User is already an admin!");
    document.getElementById('adminId').value = "";
}

async function addSub() {
    const id = document.getElementById('chId').value;
    const url = document.getElementById('chUrl').value;
    if(!id || !url) return alert("Please fill both fields!");
    
    tg.MainButton.text = "Saving Channel..."; tg.MainButton.show();
    await fetch(`${API_BASE}/api/add_sub`, {
        method: 'POST', body: JSON.stringify({channel_id: id, channel_url: url}), headers: {'Content-Type': 'application/json'}
    });
    tg.MainButton.hide();
    document.getElementById('chId').value = "";
    document.getElementById('chUrl').value = "";
    loadData();
}

async function delSub(id) {
    if(!confirm(`Are you sure you want to remove ${id}?`)) return;
    await fetch(`${API_BASE}/api/del_sub`, {
        method: 'POST', body: JSON.stringify({channel_id: id}), headers: {'Content-Type': 'application/json'}
    });
    loadData();
}

async function sendBroadcast() {
    const msg = document.getElementById('bMsg').value;
    if(!msg) return alert("Message cannot be empty!");
    
    if(confirm("Send this message to ALL users?")) {
        tg.MainButton.text = "Sending Broadcast..."; tg.MainButton.show();
        await fetch(`${API_BASE}/api/broadcast`, {
            method: 'POST', body: JSON.stringify({message: msg}), headers: {'Content-Type': 'application/json'}
        });
        alert("✅ Broadcast Sent Successfully!");
        tg.MainButton.hide();
        document.getElementById('bMsg').value = "";
    }
}

loadData();
