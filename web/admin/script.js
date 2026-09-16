const API_BASE = "https://worker-production-0420.up.railway.app"; 

const tg = window.Telegram.WebApp; 
tg.expand();

const sidebar = document.querySelector('.sidebar');
const menuToggle = document.getElementById('menuToggle');
menuToggle.addEventListener('click', (e) => { e.stopPropagation(); sidebar.classList.toggle('active'); });
document.addEventListener('click', (e) => {
    if (window.innerWidth <= 768 && sidebar.classList.contains('active')) {
        if (!sidebar.contains(e.target) && !menuToggle.contains(e.target)) sidebar.classList.remove('active');
    }
});

function switchTab(tabName) {
    document.querySelectorAll('.view-section').forEach(el => el.style.display = 'none');
    document.querySelectorAll('.nav-menu li').forEach(el => el.classList.remove('active'));
    document.getElementById(`view-${tabName}`).style.display = 'block';
    document.getElementById(`nav-${tabName}`).classList.add('active');
    if (window.innerWidth <= 768) sidebar.classList.remove('active');
}

async function loadData() {
    try {
        const res = await fetch(`${API_BASE}/api/stats`);
        const data = await res.json();
        
        document.getElementById('totalUsers').innerText = data.total_users;
        document.getElementById('activeUsers').innerText = data.active_users;
        document.getElementById('subCount').innerText = data.subs.length;
        
        if(data.settings) {
            document.getElementById('helpEmail').value = data.settings.help_email || "";
            document.getElementById('helpFb').value = data.settings.help_fb || "";
            document.getElementById('helpTg').value = data.settings.help_tg || "";
            document.getElementById('helpWa').value = data.settings.help_wa || "";
            document.getElementById('payBkash').value = data.settings.pay_bkash || "";
            document.getElementById('payNagad').value = data.settings.pay_nagad || "";
            document.getElementById('payRocket').value = data.settings.pay_rocket || "";
            document.getElementById('payCrypto').value = data.settings.pay_crypto || "";
            
            // 🔴 Render Download APIs
            const dlList = document.getElementById('dlApiList');
            dlList.innerHTML = "";
            (data.settings.download_apis || []).forEach(api => {
                dlList.innerHTML += `<li style="flex-direction:column; align-items:flex-start;">
                    <div class="api-url-text">${api}</div>
                    <div style="margin-top:10px;">
                        <button class="test-btn" onclick="testApi('${api}')"><i class="fa-solid fa-stethoscope"></i> Test</button>
                        <button class="delete-btn" style="display:inline-flex; width:auto; padding:5px 10px;" onclick="delApi('download_apis', '${api}')"><i class="fa-solid fa-trash"></i> Remove</button>
                    </div>
                </li>`;
            });

            // 🔴 Render Stream APIs
            const stList = document.getElementById('stApiList');
            stList.innerHTML = "";
            (data.settings.stream_apis || []).forEach(api => {
                stList.innerHTML += `<li style="flex-direction:column; align-items:flex-start;">
                    <div class="api-url-text">${api}</div>
                    <div style="margin-top:10px;">
                        <button class="test-btn" onclick="testApi('${api}')"><i class="fa-solid fa-stethoscope"></i> Test</button>
                        <button class="delete-btn" style="display:inline-flex; width:auto; padding:5px 10px;" onclick="delApi('stream_apis', '${api}')"><i class="fa-solid fa-trash"></i> Remove</button>
                    </div>
                </li>`;
            });
        }
        
        const tbody = document.getElementById('usersTableBody');
        tbody.innerHTML = "";
        data.users_list.forEach(u => {
            const statusHtml = u.active ? `<span class="status-dot"></span> Active` : `<span class="status-dot status-dead"></span> Blocked`;
            const vipClass = u.vip ? "vip-active" : "vip-inactive";
            const vipText = u.vip ? "⭐ VIP Member" : "Make VIP";
            tbody.innerHTML += `<tr><td>${u.id}</td><td>${statusHtml}</td><td><button class="vip-btn ${vipClass}" onclick="toggleVIP(${u.id}, ${!u.vip})">${vipText}</button></td></tr>`;
        });

        const adminList = document.getElementById('adminList');
        adminList.innerHTML = "";
        data.admins.forEach(a => {
            if(a.role === "Primary Owner") adminList.innerHTML += `<li><span>👑 ${a.id} (${a.role})</span></li>`;
            else adminList.innerHTML += `<li><span>👤 ${a.id} (${a.role})</span> <button class="delete-btn" onclick="delAdmin(${a.id})"><i class="fa-solid fa-trash"></i></button></li>`;
        });
        
        const list = document.getElementById('subList');
        list.innerHTML = "";
        data.subs.forEach(sub => {
            list.innerHTML += `<li><span><i class="fa-brands fa-telegram" style="color:#2563eb; margin-right:8px;"></i> ${sub.id}</span>
                <button class="delete-btn" onclick="delSub('${sub.id}')"><i class="fa-solid fa-trash"></i></button></li>`;
        });

        const pList = document.getElementById('planList');
        pList.innerHTML = "";
        data.plans.forEach(p => {
            pList.innerHTML += `<li style="flex-direction:column; align-items:flex-start;">
                <div style="display:flex; justify-content:space-between; width:100%;"><b style="color:var(--primary); font-size:16px;">${p.name}</b>
                <button class="delete-btn" onclick="delPlan('${p.id}')"><i class="fa-solid fa-trash"></i></button></div>
                <div style="font-size:13px; color:var(--text-muted); margin-top:5px;">⏳ Duration: ${p.duration} | 💰 Price: ${p.price}</div>
            </li>`;
        });
    } catch (e) {
        tg.showAlert("API Error! Railway লিংকটি চেক করুন।");
    }
}

// 🔴 API Management Functions
async function addApi(apiType) {
    const urlInput = (apiType === 'download_apis') ? document.getElementById('dlApiUrl') : document.getElementById('stApiUrl');
    const url = urlInput.value.trim();
    if(!url) return tg.showAlert("Please enter an API URL.");
    
    tg.MainButton.text = "Adding API..."; tg.MainButton.show();
    await fetch(`${API_BASE}/api/add_api`, { method: 'POST', body: JSON.stringify({api_type: apiType, api_url: url}), headers: {'Content-Type': 'application/json'} });
    tg.MainButton.hide();
    urlInput.value = "";
    loadData();
}

async function delApi(apiType, url) {
    if(!confirm("Remove this API?")) return;
    await fetch(`${API_BASE}/api/del_api`, { method: 'POST', body: JSON.stringify({api_type: apiType, api_url: url}), headers: {'Content-Type': 'application/json'} });
    loadData();
}

async function testApi(url) {
    tg.MainButton.text = "Testing API..."; tg.MainButton.show();
    const res = await fetch(`${API_BASE}/api/test_api`, { method: 'POST', body: JSON.stringify({api_url: url}), headers: {'Content-Type': 'application/json'} });
    const data = await res.json();
    tg.MainButton.hide();
    
    if(data.status === "Active") tg.showAlert("✅ API is ACTIVE and Responding!");
    else tg.showAlert("❌ API is DEAD or Not Responding properly!");
}

async function saveHelpSettings() {
    const settingsData = { help_email: document.getElementById('helpEmail').value, help_fb: document.getElementById('helpFb').value, help_tg: document.getElementById('helpTg').value, help_wa: document.getElementById('helpWa').value };
    tg.MainButton.text = "Saving Settings..."; tg.MainButton.show();
    await fetch(`${API_BASE}/api/update_settings`, { method: 'POST', body: JSON.stringify(settingsData), headers: {'Content-Type': 'application/json'} });
    tg.MainButton.hide(); tg.showAlert("✅ Help settings saved successfully!");
}

async function savePaymentSettings() {
    const paymentData = { pay_bkash: document.getElementById('payBkash').value, pay_nagad: document.getElementById('payNagad').value, pay_rocket: document.getElementById('payRocket').value, pay_crypto: document.getElementById('payCrypto').value };
    tg.MainButton.text = "Saving Methods..."; tg.MainButton.show();
    await fetch(`${API_BASE}/api/update_settings`, { method: 'POST', body: JSON.stringify(paymentData), headers: {'Content-Type': 'application/json'} });
    tg.MainButton.hide(); tg.showAlert("✅ Payment Methods saved successfully!");
}

async function addPlan() {
    const name = document.getElementById('pName').value, duration = document.getElementById('pDuration').value, price = document.getElementById('pPrice').value;
    if(!name || !duration || !price) return tg.showAlert("Please fill all plan fields!");
    const planId = "plan_" + Date.now(); 
    tg.MainButton.text = "Creating Plan..."; tg.MainButton.show();
    await fetch(`${API_BASE}/api/add_plan`, { method: 'POST', body: JSON.stringify({plan_id: planId, name: name, duration: duration, price: price}), headers: {'Content-Type': 'application/json'} });
    tg.MainButton.hide(); document.getElementById('pName').value = ""; document.getElementById('pDuration').value = ""; document.getElementById('pPrice').value = ""; loadData(); tg.showAlert("✅ Plan Created Successfully!");
}
async function delPlan(planId) {
    if(!confirm(`Remove this plan?`)) return;
    await fetch(`${API_BASE}/api/del_plan`, { method: 'POST', body: JSON.stringify({plan_id: planId}), headers: {'Content-Type': 'application/json'} }); loadData();
}
async function toggleVIP(userId, status) {
    await fetch(`${API_BASE}/api/toggle_vip`, { method: 'POST', body: JSON.stringify({user_id: userId, vip: status}), headers: {'Content-Type': 'application/json'} }); loadData();
}
async function addAdmin() {
    const id = document.getElementById('adminId').value, role = document.querySelector('input[name="adminRole"]:checked').value; 
    if(!id) return tg.showAlert("Enter Admin User ID!");
    await fetch(`${API_BASE}/api/add_admin`, { method: 'POST', body: JSON.stringify({user_id: id, role: role}), headers: {'Content-Type': 'application/json'} });
    document.getElementById('adminId').value = ""; loadData(); tg.showAlert("Admin Added!");
}
async function delAdmin(id) {
    if(!confirm("Remove this admin?")) return;
    await fetch(`${API_BASE}/api/del_admin`, { method: 'POST', body: JSON.stringify({user_id: id}), headers: {'Content-Type': 'application/json'} }); loadData();
}
async function addSub() {
    const id = document.getElementById('chId').value, url = document.getElementById('chUrl').value;
    if(!id || !url) return;
    await fetch(`${API_BASE}/api/add_sub`, { method: 'POST', body: JSON.stringify({channel_id: id, channel_url: url}), headers: {'Content-Type': 'application/json'} });
    document.getElementById('chId').value = ""; document.getElementById('chUrl').value = ""; loadData();
}
async function delSub(id) {
    if(!confirm(`Remove ${id}?`)) return;
    await fetch(`${API_BASE}/api/del_sub`, { method: 'POST', body: JSON.stringify({channel_id: id}), headers: {'Content-Type': 'application/json'} }); loadData();
}
function toggleSpecificInput() {
    const type = document.querySelector('input[name="bType"]:checked').value;
    document.getElementById('specificIdDiv').style.display = (type === 'specific') ? 'block' : 'none';
}
async function sendBroadcast() {
    const msg = document.getElementById('bMsg').value, type = document.querySelector('input[name="bType"]:checked').value, targetId = document.getElementById('bTargetId').value;
    if(!msg) return tg.showAlert("Message cannot be empty!");
    if(type === 'specific' && !targetId) return tg.showAlert("Enter target User ID!");
    tg.showConfirm(`Send message to ${type}?`, async function(confirmed) {
        if(confirmed) {
            tg.MainButton.text = "Sending..."; tg.MainButton.show();
            await fetch(`${API_BASE}/api/broadcast`, { method: 'POST', body: JSON.stringify({message: msg, type: type, target_id: targetId}), headers: {'Content-Type': 'application/json'} });
            tg.showAlert("✅ Message Sent!"); tg.MainButton.hide(); document.getElementById('bMsg').value = "";
        }
    });
}

loadData();
