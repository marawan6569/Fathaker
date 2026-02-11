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

    // Surah select triggers search immediately
    surahSelect.addEventListener('change', function () {
        if (surahSelect.value) doSearch();
    });

    // Search button
    searchBtn.addEventListener('click', doSearch);

    function doSearch() {
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

        var html = '';
        for (var i = 0; i < verses.length; i++) {
            var v = verses[i];
            html += buildVerseCard(v, i);
        }
        resultsContainer.innerHTML = html;
    }

    function buildVerseCard(v, index) {
        var delay = Math.min(index * 0.05, 1);
        var verseDisplay = v.verse;

        // Highlight matching text for text search modes
        if (currentQuery && (currentMode === 'search' || currentMode === 'starts-with' || currentMode === 'ends-with' || currentMode === 'surah')) {
            verseDisplay = highlightText(verseDisplay, currentQuery);
        }

        var sajdaHtml = '';
        if (v.is_sajda) {
            sajdaHtml = '<span class="sajda-badge"><i class="fas fa-pray"></i> سجدة</span>';
        }

        return '<div class="verse-card" style="animation-delay:' + delay + 's;">' +
            '<div class="verse-card-header">' +
            '<span class="verse-surah-badge"><i class="fas fa-book-open"></i> ' + escapeHtml(v.surah) + '</span>' +
            '<span class="verse-number-badge">آية ' + v.number_in_surah + '</span>' +
            sajdaHtml +
            '</div>' +
            '<p class="verse-text">' + verseDisplay + '</p>' +
            '<div class="verse-meta">' +
            '<span class="verse-meta-item"><i class="fas fa-bookmark"></i> جزء ' + v.juz + '</span>' +
            '<span class="verse-meta-item"><i class="fas fa-file-alt"></i> صفحة ' + v.page + '</span>' +
            '<span class="verse-meta-item"><i class="fas fa-layer-group"></i> ربع ' + v.the_quarter + '</span>' +
            '<span class="verse-meta-item"><i class="fas fa-hashtag"></i> رقم ' + v.number_in_quran + '</span>' +
            '</div>' +
            '</div>';
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
