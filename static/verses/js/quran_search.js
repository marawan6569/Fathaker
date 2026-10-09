document.addEventListener('DOMContentLoaded', function () {
    // Elements
    const modePills = document.querySelectorAll('.mode-pill');
    const textGroup = document.getElementById('text-input-group');
    const surahGroup = document.getElementById('surah-input-group');
    const pageGroup = document.getElementById('page-input-group');
    const rangeGroup = document.getElementById('range-input-group');
    const searchText = document.getElementById('search-text');
    const surahSelect = document.getElementById('surah-select');
    const surahSearchText = document.getElementById('surah-search-text');
    const pageNumber = document.getElementById('page-number');
    const rangeStart = document.getElementById('range-start');
    const rangeEnd = document.getElementById('range-end');
    const searchBtn = document.getElementById('search-btn');
    const loadingSpinner = document.getElementById('loading-spinner');
    const resultCount = document.getElementById('result-count');
    const countNumber = document.getElementById('count-number');
    const resultsContainer = document.getElementById('results-container');
    const emptyState = document.getElementById('empty-state');

    let currentMode = 'search';
    let currentQuery = '';

    // Input groups map
    const inputGroups = {
        'search': textGroup,
        'starts-with': textGroup,
        'ends-with': textGroup,
        'surah': surahGroup,
        'page': pageGroup,
        'range': rangeGroup,
    };

    // Placeholders for text modes
    const placeholders = {
        'search': 'اكتب كلمة أو جملة للبحث...',
        'starts-with': 'اكتب بداية الآية...',
        'ends-with': 'اكتب نهاية الآية...',
    };

    // Mode switching
    modePills.forEach(function (pill) {
        pill.addEventListener('click', function () {
            modePills.forEach(function (p) { p.classList.remove('active'); });
            pill.classList.add('active');
            modePills.forEach(p => p.setAttribute('aria-pressed', String(p === pill)));
            currentMode = pill.dataset.mode;
            switchInputGroup(currentMode);
        });
    });

    function switchInputGroup(mode) {
        // Hide all
        Object.values(inputGroups).forEach(function (g) { g.style.display = 'none'; });
        // Show relevant
        if (inputGroups[mode]) {
            inputGroups[mode].style.display = 'block';
        }
        // Update placeholder for text modes
        if (placeholders[mode]) {
            searchText.placeholder = placeholders[mode];
            searchText.focus();
        }
    }

    // Search on Enter key
    searchText.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') doSearch();
    });
    pageNumber.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') doSearch();
    });
    rangeStart.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') doSearch();
    });
    rangeEnd.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') doSearch();
    });

    // Surah search text Enter key
    surahSearchText.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') doSearch();
    });

    document.getElementById('advanced-search-btn').addEventListener('click', doSearch);
    document.getElementById('advanced-search').addEventListener('toggle', function () {
        if (this.open && ['search','starts-with','ends-with'].includes(currentMode)) document.querySelector('[data-mode="surah"]').click();
        if (!this.open && ['surah','page','range'].includes(currentMode)) document.querySelector('[data-mode="search"]').click();
    });
    let resultVerses = [], shownResults = 6;
    const moreResults = document.getElementById('search-load-more');
    moreResults.addEventListener('click', () => { shownResults += 6; paintResults(); });
    function paintResults() {
        resultsContainer.innerHTML = resultVerses.slice(0, shownResults).map(buildVerseCard).join('');
        moreResults.hidden = shownResults >= resultVerses.length;
        bindAudioButtons(); bindMutashabihatButtons();
    }
    // Search button
    searchBtn.addEventListener('click', doSearch);

    function doSearch() {
        moreResults.hidden = true;
        var url = buildUrl();
        if (!url) return;

        // Show loading, hide results
        loadingSpinner.style.display = 'block';
        resultCount.style.display = 'none';
        resultsContainer.innerHTML = '';
        emptyState.style.display = 'none';

        fetch(url)
            .then(function (res) {
                if (!res.ok) throw new Error('خطأ في الاتصال');
                return res.json();
            })
            .then(function (data) {
                loadingSpinner.style.display = 'none';
                renderResults(data);
            })
            .catch(function (err) {
                loadingSpinner.style.display = 'none';
                resultsContainer.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><p>' + err.message + '</p></div>';
            });
    }

    function buildUrl() {
        switch (currentMode) {
            case 'search':
                currentQuery = searchText.value.trim();
                if (!currentQuery) return null;
                return API_BASE + 'search/?q=' + encodeURIComponent(currentQuery);
            case 'starts-with':
                currentQuery = searchText.value.trim();
                if (!currentQuery) return null;
                return API_BASE + 'starts-with/?q=' + encodeURIComponent(currentQuery);
            case 'ends-with':
                currentQuery = searchText.value.trim();
                if (!currentQuery) return null;
                return API_BASE + 'ends-with/?q=' + encodeURIComponent(currentQuery);
            case 'surah':
                var surahId = surahSelect.value;
                if (!surahId) return null;
                var surahQuery = surahSearchText.value.trim();
                currentQuery = surahQuery;
                var surahUrl = API_BASE + 'surah/' + surahId + '/';
                if (surahQuery) {
                    surahUrl += '?q=' + encodeURIComponent(surahQuery);
                }
                return surahUrl;
            case 'page':
                var page = pageNumber.value.trim();
                if (!page) return null;
                currentQuery = '';
                return API_BASE + 'verses_list?page=' + encodeURIComponent(page);
            case 'range':
                var start = rangeStart.value.trim();
                var end = rangeEnd.value.trim();
                if (!start || !end) return null;
                currentQuery = '';
                return API_BASE + 'range/' + encodeURIComponent(start) + '/' + encodeURIComponent(end) + '/';
            default:
                return null;
        }
    }

    function renderResults(verses) {
        if (!verses || verses.length === 0) {
            emptyState.style.display = 'block';
            resultCount.style.display = 'none';
            return;
        }

        countNumber.textContent = verses.length;
        resultCount.style.display = 'block';

        document.getElementById('results-heading').textContent = currentQuery ? 'نتائج البحث عن «' + currentQuery + '»' : 'نتائج البحث';
        resultVerses = verses; shownResults = 6; paintResults();
    }

    // ===== Audio Player =====
    var audioPlayer = null;
    var currentAudioBtn = null;

    function bindAudioButtons() {
        var buttons = resultsContainer.querySelectorAll('.verse-audio-btn');
        buttons.forEach(function (btn) {
            btn.addEventListener('click', function () {
                var url = btn.getAttribute('data-audio-url');
                if (!url) return;

                // If clicking the same button that's playing, toggle pause/play
                if (currentAudioBtn === btn && audioPlayer && !audioPlayer.paused) {
                    audioPlayer.pause();
                    btn.classList.remove('playing');
                    btn.querySelector('i').className = 'fas fa-play';
                    return;
                }

                // Stop any currently playing audio
                if (audioPlayer) {
                    audioPlayer.pause();
                    if (currentAudioBtn) {
                        currentAudioBtn.classList.remove('playing');
                        currentAudioBtn.querySelector('i').className = 'fas fa-play';
                    }
                }

                // Play new audio
                audioPlayer = new Audio(url);
                currentAudioBtn = btn;
                btn.classList.add('playing');
                btn.querySelector('i').className = 'fas fa-pause';

                audioPlayer.play().catch(function () {
                    btn.classList.remove('playing');
                    btn.querySelector('i').className = 'fas fa-play';
                });

                audioPlayer.addEventListener('ended', function () {
                    btn.classList.remove('playing');
                    btn.querySelector('i').className = 'fas fa-play';
                    currentAudioBtn = null;
                });
            });
        });
    }

    function buildVerseCard(v) {
        const verseDisplay = currentQuery ? highlightText(v.verse, currentQuery) : escapeHtml(v.verse);
        const audio = v.audio?.length ? `<button class="verse-audio-btn ds-icon-button" data-audio-url="${escapeHtml(v.audio[0].url)}" aria-label="استماع للآية"><i class="fa-play" aria-hidden="true"></i></button>` : '';
        return `<article class="verse-card ds-result">
            <div class="ds-result-header"><span>سورة ${escapeHtml(v.surah)} · الآية ${v.number_in_surah}</span>${audio}</div>
            <p class="verse-text">${verseDisplay}</p>
            <p class="ds-result-meta">الجزء ${v.juz} · الصفحة ${v.page}${v.is_sajda ? ' · سجدة' : ''}</p>
            <div class="ds-result-actions"><button class="verse-mutashabihat-btn ds-button ds-secondary" data-verse-pk="${escapeHtml(v.verse_pk)}">متشابهات</button><a class="ds-button ds-secondary" href="/verses/mushaf/#page=${v.page}">في المصحف</a></div>
        </article>`;
    }

    function highlightText(text, query) {
        if (!query) return escapeHtml(text);
        // Escape special regex characters in query
        var escapedQuery = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        var regex = new RegExp('(' + escapedQuery + ')', 'gi');
        // Split by matches, escape non-match parts, wrap matches in <mark>
        var parts = text.split(regex);
        var result = '';
        for (var i = 0; i < parts.length; i++) {
            if (parts[i].match(regex)) {
                result += '<mark>' + escapeHtml(parts[i]) + '</mark>';
            } else {
                result += escapeHtml(parts[i]);
            }
        }
        return result;
    }

    function escapeHtml(str) {
        if (!str) return '';
        var div = document.createElement('div');
        div.appendChild(document.createTextNode(str));
        return div.innerHTML;
    }

    // ===== Mutashabihat Modal =====
    // Initialize shared modal
    if (typeof MutashabihatModal !== 'undefined') {
        MutashabihatModal.init();
    }

    function bindMutashabihatButtons() {
        var buttons = resultsContainer.querySelectorAll('.verse-mutashabihat-btn');
        buttons.forEach(function (btn) {
            btn.addEventListener('click', function () {
                var versePk = btn.getAttribute('data-verse-pk');
                if (typeof MutashabihatModal !== 'undefined') {
                    MutashabihatModal.open(versePk);
                }
            });
        });
    }

    function highlightText(text, query) {
        if (!query) return escapeHtml(text);
        // Escape special regex characters in query
        var escapedQuery = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        var regex = new RegExp('(' + escapedQuery + ')', 'gi');
        // Split by matches, escape non-match parts, wrap matches in <mark>
        var parts = text.split(regex);
        var result = '';
        for (var i = 0; i < parts.length; i++) {
            if (parts[i].match(regex)) {
                result += '<mark>' + escapeHtml(parts[i]) + '</mark>';
            } else {
                result += escapeHtml(parts[i]);
            }
        }
        return result;
    }

    function escapeHtml(str) {
        if (!str) return '';
        var div = document.createElement('div');
        div.appendChild(document.createTextNode(str));
        return div.innerHTML;
    }
});
