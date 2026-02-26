// ===== DOM Elements =====
const radiosContainer = document.getElementById('radios-container');
const tagsFilter = document.getElementById('tags-filter');
const emptyState = document.getElementById('empty-state');
const searchBar = document.getElementById('search');
const clearSearchBtn = document.getElementById('clear-search');

// Bottom Player
const bottomPlayer = document.getElementById('bottom-player');
const playerArt = document.getElementById('player-art');
const playerName = document.getElementById('player-name');
const playerDesc = document.getElementById('player-desc');
const playerPlayBtn = document.getElementById('player-play-btn');
const waveBars = document.getElementById('wave-bars');
const playerCloseBtn = document.getElementById('player-close-btn');
const playerExpandBtn = document.getElementById('player-expand-btn');
const volumeBtn = document.getElementById('volume-btn');
const volumeSlider = document.getElementById('volume-slider');

// Fullscreen Modal
const fullscreenModal = document.getElementById('fullscreen-modal');
const fullscreenBg = document.getElementById('fullscreen-bg');
const fullscreenArt = document.getElementById('fullscreen-art');
const fullscreenVisualizer = document.getElementById('fullscreen-visualizer');
const fullscreenName = document.getElementById('fullscreen-name');
const fullscreenDesc = document.getElementById('fullscreen-desc');
const fullscreenPlayBtn = document.getElementById('fullscreen-play-btn');
const fullscreenClose = document.getElementById('fullscreen-close');
const fullscreenVolBtn = document.getElementById('fullscreen-vol-btn');
const fullscreenVolSlider = document.getElementById('fullscreen-vol-slider');
const fullscreenLikeBtn = document.getElementById('fullscreen-like-btn');
const fullscreenLikeCount = document.getElementById('fullscreen-like-count');
const fullscreenShareBtn = document.getElementById('fullscreen-share-btn');

// Share Toast
const shareToast = document.getElementById('share-toast');

// ===== State =====
const audio = new Audio();
audio.volume = 0.8;
let currentRadio = null;
let activeTag = null;
let searchQuery = '';
let currentSort = 'default';
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

// ===== URL Helpers =====
function getLikeUrl(slug) {
    return RADIO_LIKE_URL_TEMPLATE.replace('__SLUG__', slug);
}

function getDetailUrl(slug) {
    return RADIO_DETAIL_URL_TEMPLATE.replace('__SLUG__', slug);
}

// ===== Rendering =====
function renderRadioCard(radio, index) {
    const isPlaying = currentRadio && currentRadio.src === radio.src;
    const isPaused = isPlaying && audio.paused;
    const playIcon = isPlaying && !isPaused ? 'fa-pause' : 'fa-play';
    const liked = isLiked(radio.slug);

    const tagsHtml = radio.tags.map(t => `<span class="card-tag">${t}</span>`).join('');
    const descHtml = radio.description ? `<p class="card-description">${radio.description}</p>` : '';

    return `
        <div class="col-lg-4 col-md-6 col-12 radio-col" style="animation-delay: ${index * 0.05}s">
            <div class="radio-card${isPlaying ? ' playing' : ''}" data-src="${radio.src}" data-slug="${radio.slug}">
                <div class="card-body-content">
                    <a href="${getDetailUrl(radio.slug)}" class="card-radio-name" style="text-decoration:none;color:inherit;">${radio.name}</a>
                    <div class="card-tags">${tagsHtml}</div>
                    ${descHtml}
                    <div class="card-stats-row">
                        <button class="card-play-btn" data-src="${radio.src}" aria-label="تشغيل">
                            <i class="fas ${playIcon}"></i>
                        </button>
                        <button class="card-like-btn${liked ? ' liked' : ''}" data-slug="${radio.slug}" aria-label="إعجاب">
                            <i class="fas fa-heart"></i>
                            <span>${radio.likes_count}</span>
                        </button>
                        <span class="card-stat">
                            <i class="fas fa-eye"></i>
                            <span>${radio.views_count}</span>
                        </span>
                        <button class="share-btn" data-slug="${radio.slug}" data-name="${radio.name}" aria-label="مشاركة">
                            <i class="fas fa-share-alt"></i>
                        </button>
                    </div>
                </div>
                <div class="card-img-wrapper">
                    <img src="${radio.img}" alt="${radio.name}" loading="lazy">
                </div>
            </div>
        </div>`;
}

function renderRadiosList(filtered) {
    if (filtered.length === 0) {
        radiosContainer.innerHTML = '';
        emptyState.style.display = 'block';
        return;
    }

    emptyState.style.display = 'none';
    radiosContainer.innerHTML = filtered.map(renderRadioCard).join('');

    // Attach play button listeners
    radiosContainer.querySelectorAll('.card-play-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const src = btn.dataset.src;
            const radio = radios.find(r => r.src === src);
            if (radio) handleCardClick(radio);
        });
    });

    // Attach like button listeners
    radiosContainer.querySelectorAll('.card-like-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            likeRadio(btn.dataset.slug);
        });
    });

    // Attach share button listeners
    radiosContainer.querySelectorAll('.share-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            shareRadio(btn.dataset.slug, btn.dataset.name);
        });
    });

    // Card click -> go to detail
    radiosContainer.querySelectorAll('.radio-card').forEach(card => {
        card.addEventListener('click', (e) => {
            if (e.target.closest('.card-play-btn') || e.target.closest('.card-like-btn') ||
                e.target.closest('.share-btn') || e.target.closest('.card-radio-name')) return;
            window.location.href = getDetailUrl(card.dataset.slug);
        });
    });
}

function renderTagPills() {
    const allTags = new Set();
    radios.forEach(r => r.tags.forEach(t => allTags.add(t)));

    let html = `<button class="tag-pill active" data-tag="">الكل</button>`;
    allTags.forEach(tag => {
        html += `<button class="tag-pill" data-tag="${tag}">${tag}</button>`;
    });
    tagsFilter.innerHTML = html;

    tagsFilter.querySelectorAll('.tag-pill').forEach(pill => {
        pill.addEventListener('click', () => {
            activeTag = pill.dataset.tag || null;
            tagsFilter.querySelectorAll('.tag-pill').forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
            applyFilters();
        });
    });
}

// ===== Sorting =====
function sortRadios(list) {
    const sorted = [...list];
    switch (currentSort) {
        case 'likes':
            sorted.sort((a, b) => b.likes_count - a.likes_count);
            break;
        case 'views':
            sorted.sort((a, b) => b.views_count - a.views_count);
            break;
        case 'name':
            sorted.sort((a, b) => a.name.localeCompare(b.name, 'ar'));
            break;
        default:
            sorted.sort((a, b) => a.rank - b.rank);
            break;
    }
    return sorted;
}

// Sort pill event listeners
document.querySelectorAll('.sort-pill').forEach(pill => {
    pill.addEventListener('click', () => {
        currentSort = pill.dataset.sort;
        document.querySelectorAll('.sort-pill').forEach(p => p.classList.remove('active'));
        pill.classList.add('active');
        applyFilters();
    });
});

// ===== Filtering =====
function applyFilters() {
    let filtered = radios;

    if (activeTag) {
        filtered = filtered.filter(r => r.tags.some(t => t === activeTag));
    }

    if (searchQuery) {
        const q = searchQuery.toLowerCase().trim();
        filtered = filtered.filter(r =>
            r.name.toLowerCase().includes(q) ||
            r.tags.some(t => t.toLowerCase().includes(q))
        );
    }

    filtered = sortRadios(filtered);
    renderRadiosList(filtered);
}

// ===== Audio Control =====
function handleCardClick(radio) {
    if (currentRadio && currentRadio.src === radio.src) {
        togglePlay();
    } else {
        loadAndPlay(radio);
    }
}

function loadAndPlay(radio) {
    currentRadio = radio;
    audio.src = radio.src;
    playAudio();
    showPlayer();
    updatePlayerUI();
    updateCardStates();
}

function playAudio() {
    audio.play();
    updatePlayerUI();
    updateCardStates();
    updateFullscreenUI();

    // Media Session API
    if ('mediaSession' in navigator && currentRadio) {
        navigator.mediaSession.metadata = new MediaMetadata({
            title: currentRadio.name,
            artist: 'فذكر',
            artwork: [
                { src: currentRadio.img, sizes: '512x512', type: 'image/jpeg' }
            ]
        });

        navigator.mediaSession.setActionHandler('play', () => togglePlay());
        navigator.mediaSession.setActionHandler('pause', () => togglePlay());
    }

    // Dynamic Page Title
    if (currentRadio) {
        document.title = 'فذكر | ' + currentRadio.name;
    }
}

function pauseAudio() {
    audio.pause();
    updatePlayerUI();
    updateCardStates();
    updateFullscreenUI();
}

function togglePlay() {
    if (audio.paused) {
        playAudio();
    } else {
        pauseAudio();
    }
}

function stopAndReset() {
    audio.pause();
    audio.src = '';
    currentRadio = null;
    hidePlayer();
    updateCardStates();

    // Clear Media Session and Title
    if ('mediaSession' in navigator) {
        navigator.mediaSession.metadata = null;
    }
    document.title = 'فذكر | إذاعات مباشرة';
}

function showPlayer() {
    bottomPlayer.classList.add('visible');
    document.body.classList.add('player-open');
}

function hidePlayer() {
    bottomPlayer.classList.remove('visible');
    document.body.classList.remove('player-open');
    closeFullscreen();
}

function updatePlayerUI() {
    if (!currentRadio) return;

    playerArt.src = currentRadio.img;
    playerArt.alt = currentRadio.name;
    playerName.textContent = currentRadio.name;
    playerDesc.textContent = currentRadio.description || '';

    const icon = playerPlayBtn.querySelector('i');
    if (audio.paused) {
        icon.className = 'fas fa-play';
        waveBars.classList.add('paused');
    } else {
        icon.className = 'fas fa-pause';
        waveBars.classList.remove('paused');
    }
}

function updateCardStates() {
    document.querySelectorAll('.radio-card').forEach(card => {
        const src = card.dataset.src;
        const isThis = currentRadio && currentRadio.src === src;
        const playIcon = card.querySelector('.card-play-btn i');

        card.classList.toggle('playing', isThis);

        if (playIcon) {
            if (isThis && !audio.paused) {
                playIcon.className = 'fas fa-pause';
            } else {
                playIcon.className = 'fas fa-play';
            }
        }
    });
}

// ===== Volume =====
function setVolume(val) {
    audio.volume = val;
    volumeSlider.value = val * 100;
    fullscreenVolSlider.value = val * 100;
    updateVolumeIcon();
}

function updateVolumeIcon() {
    const vol = audio.volume;
    let iconClass;
    if (vol === 0) iconClass = 'fas fa-volume-mute';
    else if (vol < 0.5) iconClass = 'fas fa-volume-down';
    else iconClass = 'fas fa-volume-up';

    volumeBtn.querySelector('i').className = iconClass;
    fullscreenVolBtn.querySelector('i').className = iconClass;
}

volumeSlider.addEventListener('input', () => {
    const val = volumeSlider.value / 100;
    audio.volume = val;
    previousVolume = val > 0 ? val : previousVolume;
    fullscreenVolSlider.value = volumeSlider.value;
    updateVolumeIcon();
});

volumeBtn.addEventListener('click', () => {
    if (audio.volume > 0) {
        previousVolume = audio.volume;
        setVolume(0);
    } else {
        setVolume(previousVolume || 0.8);
    }
});

fullscreenVolSlider.addEventListener('input', () => {
    const val = fullscreenVolSlider.value / 100;
    audio.volume = val;
    previousVolume = val > 0 ? val : previousVolume;
    volumeSlider.value = fullscreenVolSlider.value;
    updateVolumeIcon();
});

fullscreenVolBtn.addEventListener('click', () => {
    if (audio.volume > 0) {
        previousVolume = audio.volume;
        setVolume(0);
    } else {
        setVolume(previousVolume || 0.8);
    }
});

// ===== Like =====
function likeRadio(slug) {
    if (isLiked(slug)) return;

    fetch(getLikeUrl(slug), {
        method: 'POST',
        headers: {
            'X-CSRFToken': CSRF_TOKEN,
            'Content-Type': 'application/json',
        },
    })
        .then(res => res.json())
        .then(data => {
            const liked = getLikedRadios();
            liked.push(slug);
            setLikedRadios(liked);

            const radio = radios.find(r => r.slug === slug);
            if (radio) radio.likes_count = data.likes_count;

            applyFilters();
            updateFullscreenLike();
        })
        .catch(() => { });
}

// ===== Share =====
function shareRadio(slug, name) {
    const radio = radios.find(r => r.slug === slug);
    const url = window.location.origin + getDetailUrl(slug);
    const desc = radio ? radio.description : '';
    const text = name + (desc ? '\n' + desc : '') + '\n' + url;

    if (navigator.share) {
        navigator.share({ title: name + ' - فذكر', text: text, url: url }).catch(() => { });
    } else {
        copyToClipboard(text);
        showShareToast('تم نسخ الرابط');
    }
}

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

// ===== Fullscreen Modal =====
function openFullscreen() {
    if (!currentRadio) return;
    fullscreenArt.src = currentRadio.img;
    fullscreenBg.style.backgroundImage = `url('${currentRadio.img}')`;
    fullscreenName.textContent = currentRadio.name;
    fullscreenDesc.textContent = currentRadio.description || '';
    fullscreenVolSlider.value = audio.volume * 100;
    updateFullscreenUI();
    updateFullscreenLike();
    fullscreenModal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeFullscreen() {
    fullscreenModal.classList.remove('active');
    document.body.style.overflow = '';
}

function updateFullscreenUI() {
    if (!currentRadio) return;
    const icon = fullscreenPlayBtn.querySelector('i');
    if (audio.paused) {
        icon.className = 'fas fa-play';
        fullscreenVisualizer.classList.add('paused');
    } else {
        icon.className = 'fas fa-pause';
        fullscreenVisualizer.classList.remove('paused');
    }
}

function updateFullscreenLike() {
    if (!currentRadio) return;
    const liked = isLiked(currentRadio.slug);
    fullscreenLikeBtn.classList.toggle('liked', liked);
    fullscreenLikeCount.textContent = currentRadio.likes_count;
}

playerExpandBtn.addEventListener('click', openFullscreen);
fullscreenClose.addEventListener('click', closeFullscreen);

fullscreenPlayBtn.addEventListener('click', () => {
    togglePlay();
});

fullscreenLikeBtn.addEventListener('click', () => {
    if (currentRadio) likeRadio(currentRadio.slug);
});

fullscreenShareBtn.addEventListener('click', () => {
    if (currentRadio) shareRadio(currentRadio.slug, currentRadio.name);
});

// Close on Escape
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && fullscreenModal.classList.contains('active')) {
        closeFullscreen();
    }
});

// ===== Event Listeners =====

// Search
searchBar.addEventListener('input', () => {
    searchQuery = searchBar.value;
    applyFilters();
});

// Clear search
clearSearchBtn.addEventListener('click', () => {
    searchBar.value = '';
    searchQuery = '';
    searchBar.focus();
    applyFilters();
});

// Bottom player play/pause
playerPlayBtn.addEventListener('click', () => {
    togglePlay();
});

// Bottom player close
playerCloseBtn.addEventListener('click', () => {
    stopAndReset();
});

// ===== Init =====
renderTagPills();
applyFilters();
