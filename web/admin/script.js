const tg = window.Telegram.WebApp; 
tg.expand();

const params = new URLSearchParams(window.location.search);
const API_BASE = params.get('api') || "";

async function loadData() {
    if(!API_BASE) return;
    const res = await fetch(`${API_BASE}/api/stats`);
    const data = await res.json();
    
    document.getElementById('userCount').innerText = data.users;
    
    const list = document.getElementById('subList');
    list.innerHTML = "";
    data.subs.forEach(sub => {
        list.innerHTML += `<li>${sub.id} <button onclick="delSub('${sub.id}')">❌</button></li>`;
    });
}

async function addSub() {
    const id = document.getElementById('chId').value;
    const url = document.getElementById('chUrl').value;
    if(!id || !url) return alert("Please fill both fields");
    
    tg.MainButton.text = "Saving..."; tg.MainButton.show();
    await fetch(`${API_BASE}/api/add_sub`, {
        method: 'POST', body: JSON.stringify({channel_id: id, channel_url: url}), headers: {'Content-Type': 'application/json'}
    });
    tg.MainButton.hide();
    document.getElementById('chId').value = "";
    document.getElementById('chUrl').value = "";
    loadData();
}

async function delSub(id) {
    if(!confirm(`Delete ${id}?`)) return;
    await fetch(`${API_BASE}/api/del_sub`, {
        method: 'POST', body: JSON.stringify({channel_id: id}), headers: {'Content-Type': 'application/json'}
    });
    loadData();
}

async function sendBroadcast() {
    const msg = document.getElementById('bMsg').value;
    if(!msg) return alert("Message is empty");
    
    if(confirm("Send to all users?")) {
        tg.MainButton.text = "Sending..."; tg.MainButton.show();
        await fetch(`${API_BASE}/api/broadcast`, {
            method: 'POST', body: JSON.stringify({message: msg}), headers: {'Content-Type': 'application/json'}
        });
        alert("Broadcast Sent!");
        tg.MainButton.hide();
        document.getElementById('bMsg').value = "";
    }
}

loadData();
