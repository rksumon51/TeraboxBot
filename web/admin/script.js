const tg = window.Telegram.WebApp;
tg.expand(); // টেলিগ্রামের ফুল স্ক্রিন মোড অন করা

function addAdmin() {
    const id = document.getElementById('new-admin-id').value;
    const role = document.getElementById('new-admin-role').value;
    
    if(!id) {
        tg.showAlert("⚠️ অনুগ্রহ করে একটি টেলিগ্রাম আইডি দিন!");
        return;
    }
    
    // (এখানে পাইথন সার্ভারে রিকোয়েস্ট পাঠানোর API কল বসবে)
    tg.showAlert(`✅ সফল! ${id} কে ${role} হিসেবে সেট করা হয়েছে।`);
    document.getElementById('new-admin-id').value = "";
}
