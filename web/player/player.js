const tg = window.Telegram.WebApp;
tg.expand();

// URL থেকে link এবং title বের করা
const urlParams = new URLSearchParams(window.location.search);
const videoLink = urlParams.get('link');
const videoTitle = urlParams.get('title') || 'Terabox Video';

// Title সেট করা
document.getElementById('video-title').innerText = videoTitle;

// Video Source সেট করা
if (videoLink) {
    document.getElementById('video-player').src = videoLink;
} else {
    document.getElementById('video-title').innerText = "❌ Error: Video link not found!";
}

// Download Button লজিক
function downloadVideo() {
    if (videoLink) {
        // টেলিগ্রামের বাইরে ব্রাউজারে লিংক ওপেন করে ডাউনলোড শুরু করবে
        tg.openLink(videoLink);
    } else {
        tg.showAlert("ডাউনলোড লিংক পাওয়া যায়নি!");
    }
}
