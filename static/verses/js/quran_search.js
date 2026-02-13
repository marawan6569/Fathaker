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

    // ===== Custom Surah Dropdown =====
    var surahDropdown = document.getElementById('surah-dropdown');
    var surahTrigger = document.getElementById('surah-dropdown-trigger');
    var surahLabel = document.getElementById('surah-dropdown-label');
    var surahPanel = document.getElementById('surah-dropdown-panel');
    var surahFilter = document.getElementById('surah-dropdown-filter');
    var surahList = document.getElementById('surah-dropdown-list');
    var surahItems = surahList.querySelectorAll('.surah-dropdown-item');

    // Toggle dropdown
    surahTrigger.addEventListener('click', function (e) {
        e.stopPropagation();
        var isOpen = surahDropdown.classList.contains('open');
        if (isOpen) {
            closeSurahDropdown();
        } else {
            surahDropdown.classList.add('open');
            surahFilter.value = '';
            filterSurahItems('');
            setTimeout(function () { surahFilter.focus(); }, 100);
        }
    });

    // Filter surahs as user types
    surahFilter.addEventListener('input', function () {
        filterSurahItems(surahFilter.value.trim());
    });

    // Prevent filter input clicks from closing dropdown
    surahFilter.addEventListener('click', function (e) {
        e.stopPropagation();
    });

    function filterSurahItems(query) {
        var visibleCount = 0;
        surahItems.forEach(function (item) {
            var name = item.getAttribute('data-name');
            var num = item.getAttribute('data-value');
            if (!query || name.indexOf(query) !== -1 || num === query) {
                item.style.display = '';
                visibleCount++;
            } else {
                item.style.display = 'none';
            }
        });
        // Show empty message
        var existingEmpty = surahList.querySelector('.surah-dropdown-empty');
        if (visibleCount === 0) {
            if (!existingEmpty) {
                var emptyEl = document.createElement('li');
                emptyEl.className = 'surah-dropdown-empty';
                emptyEl.textContent = 'لا توجد نتائج';
                surahList.appendChild(emptyEl);
            }
        } else if (existingEmpty) {
            existingEmpty.remove();
        }
    }

    // Select a surah item
    surahItems.forEach(function (item) {
        item.addEventListener('click', function (e) {
            e.stopPropagation();
            var value = item.getAttribute('data-value');
            var name = item.getAttribute('data-name');

            // Update hidden input & label
            surahSelect.value = value;
            surahLabel.textContent = name;
            surahTrigger.classList.add('has-value');

            // Mark selected
            surahItems.forEach(function (i) { i.classList.remove('selected'); });
            item.classList.add('selected');

            closeSurahDropdown();
            doSearch();
        });
    });

    function closeSurahDropdown() {
        surahDropdown.classList.remove('open');
    }

    // Close dropdown on outside click
    document.addEventListener('click', function (e) {
        if (!surahDropdown.contains(e.target)) {
            closeSurahDropdown();
        }
    });

    // Close dropdown when switching modes
    modePills.forEach(function (pill) {
        pill.addEventListener('click', function () {
            closeSurahDropdown();
        });
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
        bindAudioButtons();
        bindMutashabihatButtons();
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

        // Audio button
        var audioHtml = '';
        if (v.audio && v.audio.length > 0) {
            audioHtml = '<button class="verse-audio-btn" data-audio-url="' + escapeHtml(v.audio[0].url) + '" title="تشغيل">' +
                '<i class="fas fa-play"></i>' +
                '</button>';
        }

        // Mutashabihat button
        var mutashabihatHtml = '<button class="verse-mutashabihat-btn" data-verse-pk="' + escapeHtml(v.verse_pk) + '" title="المتشابهات">' +
            '<i class="fas fa-clone"></i>' +
            '<span>متشابهات</span>' +
            '</button>';

        return '<div class="verse-card" style="animation-delay:' + delay + 's;">' +
            '<div class="verse-card-header">' +
            '<span class="verse-surah-badge"><i class="fas fa-book-open"></i> ' + escapeHtml(v.surah) + '</span>' +
            '<span class="verse-number-badge">آية ' + v.number_in_surah + '</span>' +
            sajdaHtml +
            audioHtml +
            mutashabihatHtml +
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

    // ===== Mutashabihat Modal =====
    var mutashabihatModal = document.getElementById('mutashabihat-modal');
    var mutashabihatOverlay = document.getElementById('mutashabihat-overlay');
    var mutashabihatClose = document.getElementById('mutashabihat-close');
    var mutashabihatBody = document.getElementById('mutashabihat-body');
    var mutashabihatTitle = document.getElementById('mutashabihat-title');

    function bindMutashabihatButtons() {
        var buttons = resultsContainer.querySelectorAll('.verse-mutashabihat-btn');
        buttons.forEach(function (btn) {
            btn.addEventListener('click', function () {
                var versePk = btn.getAttribute('data-verse-pk');
                openMutashabihatModal(versePk);
            });
        });
    }

    function openMutashabihatModal(versePk) {
        mutashabihatTitle.textContent = 'متشابهات الآية ' + versePk;
        mutashabihatBody.innerHTML = '<div class="mutashabihat-loading"><div class="spinner"></div><p>جاري التحميل...</p></div>';
        mutashabihatModal.classList.add('open');
        document.body.style.overflow = 'hidden';

        fetch(API_BASE + 'mutashabihat/by-ayah/?ayah=' + encodeURIComponent(versePk))
            .then(function (res) {
                if (!res.ok) throw new Error('خطأ في الاتصال');
                return res.json();
            })
            .then(function (phrases) {
                renderMutashabihatModal(phrases, versePk);
            })
            .catch(function (err) {
                mutashabihatBody.innerHTML = '<div class="mutashabihat-empty"><i class="fas fa-exclamation-triangle"></i><p>' + err.message + '</p></div>';
            });
    }

    function closeMutashabihatModal() {
        mutashabihatModal.classList.remove('open');
        document.body.style.overflow = '';
    }

    mutashabihatClose.addEventListener('click', closeMutashabihatModal);
    mutashabihatOverlay.addEventListener('click', closeMutashabihatModal);
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && mutashabihatModal.classList.contains('open')) {
            closeMutashabihatModal();
        }
    });

    function highlightWords(verseText, wordFrom, wordTo) {
        var words = verseText.split(' ');
        var result = '';
        for (var i = 0; i < words.length; i++) {
            var wordNum = i + 1;
            if (wordNum >= wordFrom && wordNum <= wordTo) {
                result += '<mark>' + escapeHtml(words[i]) + '</mark>';
            } else {
                result += escapeHtml(words[i]);
            }
            if (i < words.length - 1) result += ' ';
        }
        return result;
    }

    function renderMutashabihatModal(phrases, currentVersePk) {
        if (!phrases || phrases.length === 0) {
            mutashabihatBody.innerHTML = '<div class="mutashabihat-empty"><i class="fas fa-check-circle"></i><p>لا توجد متشابهات لهذه الآية</p></div>';
            return;
        }

        var html = '<div class="mutashabihat-count">' + phrases.length + ' عبارة متشابهة</div>';

        for (var i = 0; i < phrases.length; i++) {
            var phrase = phrases[i];
            html += '<div class="mutashabihat-phrase">';
            html += '<div class="mutashabihat-phrase-header">';
            html += '<span class="mutashabihat-phrase-id">عبارة #' + phrase.phrase_id + '</span>';
            html += '<span class="mutashabihat-phrase-stats">' + phrase.occurrences_count + ' تكرار في ' + phrase.surahs_count + ' سورة</span>';
            html += '</div>';

            // Source verse
            html += '<div class="mutashabihat-source">';
            html += '<div class="mutashabihat-source-label"><i class="fas fa-star"></i> المصدر</div>';
            html += '<div class="mutashabihat-verse-text">' + highlightWords(phrase.source_verse.verse, phrase.source_word_from, phrase.source_word_to) + '</div>';
            html += '<div class="mutashabihat-verse-ref">' + escapeHtml(phrase.source_verse.surah) + ' - آية ' + phrase.source_verse.number_in_surah;
            html += ' <span class="mutashabihat-word-range">(كلمات ' + phrase.source_word_from + '-' + phrase.source_word_to + ')</span>';
            html += '</div>';
            html += '</div>';

            // Occurrences
            html += '<div class="mutashabihat-occurrences-label"><i class="fas fa-clone"></i> المواضع (' + phrase.occurrences.length + ')</div>';
            html += '<div class="mutashabihat-occurrences">';
            for (var j = 0; j < phrase.occurrences.length; j++) {
                var occ = phrase.occurrences[j];
                var isCurrentVerse = occ.verse.verse_pk === currentVersePk;
                html += '<div class="mutashabihat-occ' + (isCurrentVerse ? ' current' : '') + '">';
                html += '<div class="mutashabihat-occ-text">' + highlightWords(occ.verse.verse, occ.word_from, occ.word_to) + '</div>';
                html += '<div class="mutashabihat-occ-ref">';
                html += '<span class="mutashabihat-occ-surah">' + escapeHtml(occ.verse.surah) + '</span>';
                html += '<span class="mutashabihat-occ-ayah">آية ' + occ.verse.number_in_surah + '</span>';
                html += '<span class="mutashabihat-word-range">كلمات ' + occ.word_from + '-' + occ.word_to + '</span>';
                if (isCurrentVerse) html += '<span class="mutashabihat-current-tag">الآية الحالية</span>';
                html += '</div>';
                html += '</div>';
            }
            html += '</div>';
            html += '</div>';
        }

        mutashabihatBody.innerHTML = html;
    }
});
