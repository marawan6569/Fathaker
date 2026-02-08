// ===== DOM Elements =====
const detailPlayBtn = document.getElementById('detail-play-btn');
const detailVisualizer = document.getElementById('detail-visualizer');
const detailVolBtn = document.getElementById('detail-vol-btn');
const detailVolSlider = document.getElementById('detail-vol-slider');
const detailLikeBtn = document.getElementById('detail-like-btn');
const detailLikesCount = document.getElementById('detail-likes-count');
const detailShareBtn = document.getElementById('detail-share-btn');
const shareToast = document.getElementById('share-toast');

// ===== State =====
const audio = new Audio();
audio.volume = 0.8;
let isPlaying = false;
let previousVolume = 0.8;

// Liked radios tracking
function getLikedRadios() {
    try {
        return JSON.parse(localStorage.getItem('fathaker_liked_radios') || '[]');
    } catch { return []; }
}

function setLikedRadios(liked) {
    localStorage.setItem('fathaker_liked_radios', JSON.stringify(liked));
}

function isLiked(slug) {
    return getLikedRadios().includes(slug);
}

// ===== Play / Pause =====
function togglePlay() {
    if (audio.paused) {
        audio.src = RADIO_DATA.src;
        audio.play();
        isPlaying = true;
    } else {
        audio.pause();
        isPlaying = false;
    }
    updatePlayUI();
}

function updatePlayUI() {
    const icon = detailPlayBtn.querySelector('i');
    if (audio.paused) {
        icon.className = 'fas fa-play';
        detailVisualizer.classList.add('paused');
    } else {
        icon.className = 'fas fa-pause';
        detailVisualizer.classList.remove('paused');
    }
}

detailPlayBtn.addEventListener('click', togglePlay);

// ===== Volume =====
function setVolume(val) {
    audio.volume = val;
    detailVolSlider.value = val * 100;
    updateVolumeIcon();
}

function updateVolumeIcon() {
    const vol = audio.volume;
    let iconClass;
    if (vol === 0) iconClass = 'fas fa-volume-mute';
    else if (vol < 0.5) iconClass = 'fas fa-volume-down';
    else iconClass = 'fas fa-volume-up';
    detailVolBtn.querySelector('i').className = iconClass;
}

detailVolSlider.addEventListener('input', () => {
    const val = detailVolSlider.value / 100;
    audio.volume = val;
    previousVolume = val > 0 ? val : previousVolume;
    updateVolumeIcon();
});

detailVolBtn.addEventListener('click', () => {
    if (audio.volume > 0) {
        previousVolume = audio.volume;
        setVolume(0);
    } else {
        setVolume(previousVolume || 0.8);
    }
});

// ===== Like =====
function updateLikeUI() {
    const liked = isLiked(RADIO_DATA.slug);
    detailLikeBtn.classList.toggle('liked', liked);
}

detailLikeBtn.addEventListener('click', () => {
    if (isLiked(RADIO_DATA.slug)) return;

    fetch(RADIO_LIKE_URL, {
        method: 'POST',
        headers: {
            'X-CSRFToken': CSRF_TOKEN,
            'Content-Type': 'application/json',
        },
    })
    .then(res => res.json())
    .then(data => {
        const liked = getLikedRadios();
        liked.push(RADIO_DATA.slug);
        setLikedRadios(liked);
        detailLikesCount.textContent = data.likes_count;
        updateLikeUI();
    })
    .catch(() => {});
});

// ===== Share =====
detailShareBtn.addEventListener('click', () => {
    const name = RADIO_DATA.name;
    const desc = RADIO_DATA.description || '';
    const imgUrl = window.location.origin + RADIO_DATA.img;
    const pageUrl = RADIO_DETAIL_URL;
    const text = name + (desc ? '\n' + desc : '') + '\n' + pageUrl;

    if (navigator.share) {
        navigator.share({ title: name + ' - فذكر', text: text, url: pageUrl }).catch(() => {});
    } else {
        copyToClipboard(text);
        showShareToast('تم نسخ الرابط');
    }
});

function copyToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).catch(() => fallbackCopy(text));
    } else {
        fallbackCopy(text);
    }
}

function fallbackCopy(text) {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
}

let toastTimeout;
function showShareToast(message) {
    shareToast.textContent = message;
    shareToast.classList.add('show');
    clearTimeout(toastTimeout);
    toastTimeout = setTimeout(() => {
        shareToast.classList.remove('show');
    }, 2000);
}

// ===== Init =====
updateLikeUI();
