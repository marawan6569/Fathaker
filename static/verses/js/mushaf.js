document.addEventListener('DOMContentLoaded', function () {
    // ===== Elements =====
    var pageInput = document.getElementById('page-input');
    var nextBtn = document.getElementById('next-page-btn');
    var prevBtn = document.getElementById('prev-page-btn');
    var surahJump = document.getElementById('surah-jump');
    var juzLabel = document.getElementById('juz-label');
    var surahLabel = document.getElementById('surah-label');
    var loadingEl = document.getElementById('mushaf-loading');
    var pageContainer = document.getElementById('mushaf-page-container');
    var pageContent = document.getElementById('mushaf-page-content');
    var pageNumberEl = document.getElementById('mushaf-page-number');

    // Audio bar elements
    var audioBar = document.getElementById('audio-bar');
    var audioPlayPauseBtn = document.getElementById('audio-play-pause-btn');
    var audioPlayPauseIcon = document.getElementById('audio-play-pause-icon');
    var audioStopBtn = document.getElementById('audio-stop-btn');
    var audioInfo = document.getElementById('audio-info');

    var currentPage = 1;
    var totalPages = 604;
    var isLoading = false;
    var pageCache = {};

    // Surah first pages lookup
    var surahFirstPages = {};

    // ===== Audio State =====
    var audioPlayer = new Audio();
    var currentPlayingVerse = null; // { number_in_quran, surah_name, number_in_surah, audio_url, page }
    var currentPageVerses = []; // Array of verse data for the current page
    var isPlaying = false;
    var autoPlayNext = true;

    // Arabic numerals
    var arabicNumerals = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'];

    function toArabicNum(num) {
        return String(num).split('').map(function (d) {
            return arabicNumerals[parseInt(d)] || d;
        }).join('');
    }

    // ===== Initialization =====
    var hashPage = getPageFromHash();
    if (hashPage) {
        currentPage = hashPage;
        pageInput.value = currentPage;
    }

    loadPage(currentPage);

    // ===== Page Loading =====
    function loadPage(pageNum, direction, thenPlayVerse) {
        if (isLoading) return;
        pageNum = Math.max(1, Math.min(totalPages, pageNum));

        if (pageCache[pageNum]) {
            renderPage(pageCache[pageNum], direction, thenPlayVerse);
            return;
        }

        isLoading = true;
        showLoading();

        fetch(MUSHAF_API + '?page=' + pageNum)
            .then(function (res) {
                if (!res.ok) throw new Error('فشل تحميل الصفحة');
                return res.json();
            })
            .then(function (data) {
                pageCache[pageNum] = data;
                renderPage(data, direction, thenPlayVerse);
                isLoading = false;

                prefetchPage(pageNum + 1);
                prefetchPage(pageNum - 1);
            })
            .catch(function (err) {
                isLoading = false;
                hideLoading();
                pageContent.innerHTML = '<div style="text-align:center;padding:3rem;color:#c45e36;font-size:1.1rem;font-weight:600;"><i class="fas fa-exclamation-triangle"></i> ' + err.message + '</div>';
                pageContainer.style.display = 'flex';
            });
    }

    function prefetchPage(pageNum) {
        if (pageNum < 1 || pageNum > totalPages || pageCache[pageNum]) return;
        fetch(MUSHAF_API + '?page=' + pageNum)
            .then(function (res) { return res.json(); })
            .then(function (data) { pageCache[pageNum] = data; })
            .catch(function () { /* silent */ });
    }

    function showLoading() {
        loadingEl.style.display = 'block';
        pageContainer.style.display = 'none';
    }

    function hideLoading() {
        loadingEl.style.display = 'none';
    }

    // ===== Rendering =====
    function renderPage(data, direction, thenPlayVerse) {
        currentPage = data.page;
        pageInput.value = currentPage;
        currentPageVerses = data.verses;

        // Update info badges
        juzLabel.textContent = 'الجزء ' + toArabicNum(data.juz);

        if (data.surahs_on_page && data.surahs_on_page.length > 0) {
            var surahNames = data.surahs_on_page.map(function (s) { return s.name; });
            surahLabel.textContent = surahNames.join(' - ');

            data.surahs_on_page.forEach(function (s) {
                if (!surahFirstPages[s.id]) {
                    surahFirstPages[s.id] = currentPage;
                }
            });
        }

        updateHash(currentPage);

        // Build page HTML
        var html = '';
        var currentSurahId = null;

        for (var i = 0; i < data.verses.length; i++) {
            var v = data.verses[i];

            if (v.is_first_in_surah) {
                if (currentSurahId !== null) {
                    html += '</div>';
                }
                html += buildSurahHeader(v.surah_name, v.surah_id);
                currentSurahId = v.surah_id;
                html += '<div class="mushaf-verse-block">';
            } else if (currentSurahId === null || currentSurahId !== v.surah_id) {
                if (currentSurahId === null) {
                    html += '<div class="mushaf-verse-block">';
                }
                currentSurahId = v.surah_id;
            }

            // Verse text — clickable with data attributes
            var verseClasses = 'mushaf-verse-text';
            if (currentPlayingVerse && currentPlayingVerse.number_in_quran === v.number_in_quran) {
                verseClasses += ' verse-playing';
            }

            html += '<span class="' + verseClasses + '"'
                + ' data-verse-num="' + v.number_in_quran + '"'
                + ' data-surah-id="' + v.surah_id + '"'
                + ' data-surah-name="' + escapeAttr(v.surah_name) + '"'
                + ' data-number-in-surah="' + v.number_in_surah + '"'
                + ' data-audio-url="' + escapeAttr(v.audio_url || '') + '"'
                + ' data-page="' + currentPage + '"'
                + '>';
            html += '<i class="fas fa-play verse-play-icon"></i>';
            html += escapeHtml(v.verse);
            html += '</span>';

            if (v.is_sajda) {
                html += '<span class="mushaf-sajda-marker">سجدة</span>';
            }

            html += '<span class="mushaf-ayah-marker"><span>' + toArabicNum(v.number_in_surah) + '</span></span>';
        }

        if (currentSurahId !== null) {
            html += '</div>';
        }

        pageContent.innerHTML = html;
        pageNumberEl.textContent = toArabicNum(currentPage);

        // Attach verse click listeners
        attachVerseListeners();

        // Apply page turn animation
        hideLoading();
        pageContainer.style.display = 'flex';

        if (direction) {
            pageContainer.classList.remove('turning-next', 'turning-prev');
            void pageContainer.offsetWidth;
            pageContainer.classList.add(direction === 'next' ? 'turning-next' : 'turning-prev');
            setTimeout(function () {
                pageContainer.classList.remove('turning-next', 'turning-prev');
            }, 450);
        }

        // Auto-play first verse on new page if triggered by auto-advance
        if (thenPlayVerse) {
            setTimeout(function () {
                var firstVerseOnPage = data.verses[0];
                if (firstVerseOnPage) {
                    playVerse(firstVerseOnPage.number_in_quran);
                }
            }, 100);
        }
    }

    function buildSurahHeader(surahName, surahId) {
        var html = '<div class="mushaf-surah-header">';
        html += '<div class="mushaf-surah-name-banner">سُورَةُ ' + escapeHtml(surahName) + '</div>';
        html += '</div>';

        if (surahId !== 1 && surahId !== 9) {
            html += '<div class="mushaf-bismillah">بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ</div>';
        }

        return html;
    }

    // ===== Verse Click Handling =====
    function attachVerseListeners() {
        var verseEls = pageContent.querySelectorAll('.mushaf-verse-text');
        for (var i = 0; i < verseEls.length; i++) {
            verseEls[i].addEventListener('click', onVerseClick);
        }
    }

    function onVerseClick(e) {
        var el = e.currentTarget;
        var verseNum = parseInt(el.getAttribute('data-verse-num'));

        // If clicking the same verse that's playing, toggle pause
        if (currentPlayingVerse && currentPlayingVerse.number_in_quran === verseNum && isPlaying) {
            pauseAudio();
            return;
        }

        if (currentPlayingVerse && currentPlayingVerse.number_in_quran === verseNum && !isPlaying) {
            resumeAudio();
            return;
        }

        playVerse(verseNum);
    }

    // ===== Audio Playback =====
    function playVerse(verseNum) {
        // Find the verse data
        var verseData = findVerseData(verseNum);
        if (!verseData) return;

        var audioUrl = verseData.audio_url;
        if (!audioUrl) {
            // No audio available, skip to next
            if (autoPlayNext) {
                playNextVerse(verseNum);
            }
            return;
        }

        // Stop current audio
        audioPlayer.pause();
        audioPlayer.currentTime = 0;

        // Update state
        currentPlayingVerse = {
            number_in_quran: verseData.number_in_quran,
            surah_name: verseData.surah_name,
            number_in_surah: verseData.number_in_surah,
            audio_url: audioUrl,
            page: currentPage
        };
        isPlaying = true;

        // Update UI
        highlightPlayingVerse(verseNum);
        showAudioBar(verseData.surah_name, verseData.number_in_surah);
        audioPlayPauseIcon.className = 'fas fa-pause';

        // Play audio
        audioPlayer.src = audioUrl;
        audioPlayer.play().catch(function (err) {
            console.error('Audio play failed:', err);
            isPlaying = false;
        });
    }

    function pauseAudio() {
        audioPlayer.pause();
        isPlaying = false;
        audioPlayPauseIcon.className = 'fas fa-play';
    }

    function resumeAudio() {
        audioPlayer.play().catch(function () { });
        isPlaying = true;
        audioPlayPauseIcon.className = 'fas fa-pause';
    }

    function stopAudio() {
        audioPlayer.pause();
        audioPlayer.currentTime = 0;
        audioPlayer.src = '';
        isPlaying = false;
        currentPlayingVerse = null;
        clearVerseHighlights();
        hideAudioBar();
    }

    // When audio ends, auto-play the next verse
    audioPlayer.addEventListener('ended', function () {
        if (!autoPlayNext || !currentPlayingVerse) {
            stopAudio();
            return;
        }

        playNextVerse(currentPlayingVerse.number_in_quran);
    });

    function playNextVerse(currentVerseNum) {
        var nextVerseNum = currentVerseNum + 1;

        // Check if next verse is on the current page
        var nextVerseOnPage = findVerseData(nextVerseNum);

        if (nextVerseOnPage) {
            // Same page, just play it
            playVerse(nextVerseNum);
        } else {
            // Next verse is on the next page — flip the page
            var nextPage = currentPage + 1;
            if (nextPage > totalPages) {
                // End of Quran
                stopAudio();
                return;
            }

            // Load the next page and auto-play the first verse
            goToPage(nextPage, 'next', true);
        }
    }

    function findVerseData(verseNum) {
        for (var i = 0; i < currentPageVerses.length; i++) {
            if (currentPageVerses[i].number_in_quran === verseNum) {
                return currentPageVerses[i];
            }
        }
        return null;
    }

    // ===== Audio UI =====
    function highlightPlayingVerse(verseNum) {
        clearVerseHighlights();
        var el = pageContent.querySelector('[data-verse-num="' + verseNum + '"]');
        if (el) {
            el.classList.add('verse-playing');
        }
    }

    function clearVerseHighlights() {
        var playing = pageContent.querySelectorAll('.verse-playing');
        for (var i = 0; i < playing.length; i++) {
            playing[i].classList.remove('verse-playing');
        }
        var selected = pageContent.querySelectorAll('.verse-selected');
        for (var j = 0; j < selected.length; j++) {
            selected[j].classList.remove('verse-selected');
        }
    }

    function showAudioBar(surahName, numberInSurah) {
        audioInfo.textContent = surahName + ' - آية ' + toArabicNum(numberInSurah);
        audioBar.classList.remove('hidden');
    }

    function hideAudioBar() {
        audioBar.classList.add('hidden');
    }

    // Audio bar buttons
    audioPlayPauseBtn.addEventListener('click', function () {
        if (!currentPlayingVerse) return;
        if (isPlaying) {
            pauseAudio();
        } else {
            resumeAudio();
        }
    });

    audioStopBtn.addEventListener('click', function () {
        stopAudio();
    });

    // ===== Navigation =====
    function goToPage(pageNum, direction, autoPlay) {
        pageNum = Math.max(1, Math.min(totalPages, pageNum));
        if (pageNum === currentPage && pageCache[pageNum] && !autoPlay) return;
        loadPage(pageNum, direction, autoPlay);
    }

    // Right chevron = previous page (RTL: right side = going back)
    nextBtn.addEventListener('click', function () {
        if (currentPage > 1) {
            goToPage(currentPage - 1, 'prev');
        }
    });

    // Left chevron = next page (RTL: left side = going forward)
    prevBtn.addEventListener('click', function () {
        if (currentPage < totalPages) {
            goToPage(currentPage + 1, 'next');
        }
    });

    // Page input
    pageInput.addEventListener('change', function () {
        var page = parseInt(pageInput.value);
        if (!isNaN(page) && page >= 1 && page <= totalPages) {
            goToPage(page);
        } else {
            pageInput.value = currentPage;
        }
    });

    pageInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
            pageInput.blur();
            var page = parseInt(pageInput.value);
            if (!isNaN(page) && page >= 1 && page <= totalPages) {
                goToPage(page);
            } else {
                pageInput.value = currentPage;
            }
        }
    });

    // Surah jump
    surahJump.addEventListener('change', function () {
        var surahId = parseInt(surahJump.value);
        if (isNaN(surahId)) return;

        if (surahFirstPages[surahId]) {
            goToPage(surahFirstPages[surahId]);
            surahJump.value = '';
            return;
        }

        fetch('/verses/api/surah/' + surahId + '/')
            .then(function (res) { return res.json(); })
            .then(function (data) {
                if (data && data.length > 0) {
                    var firstPage = data[0].page;
                    surahFirstPages[surahId] = firstPage;
                    goToPage(firstPage);
                }
            })
            .catch(function () { /* silent */ });

        surahJump.value = '';
    });

    // Keyboard navigation
    document.addEventListener('keydown', function (e) {
        if (document.activeElement.tagName === 'INPUT' || document.activeElement.tagName === 'SELECT') return;

        if (e.key === 'ArrowRight') {
            e.preventDefault();
            if (currentPage > 1) {
                goToPage(currentPage - 1, 'prev');
            }
        } else if (e.key === 'ArrowLeft') {
            e.preventDefault();
            if (currentPage < totalPages) {
                goToPage(currentPage + 1, 'next');
            }
        } else if (e.key === ' ') {
            // Space to toggle play/pause
            if (currentPlayingVerse) {
                e.preventDefault();
                if (isPlaying) {
                    pauseAudio();
                } else {
                    resumeAudio();
                }
            }
        } else if (e.key === 'Escape') {
            // Escape to stop audio
            if (currentPlayingVerse) {
                e.preventDefault();
                stopAudio();
            }
        }
    });

    // ===== Touch/Swipe Support =====
    var touchStartX = 0;
    var touchEndX = 0;
    var mushafBook = document.getElementById('mushaf-book');

    mushafBook.addEventListener('touchstart', function (e) {
        touchStartX = e.changedTouches[0].screenX;
    }, { passive: true });

    mushafBook.addEventListener('touchend', function (e) {
        touchEndX = e.changedTouches[0].screenX;
        handleSwipe();
    }, { passive: true });

    function handleSwipe() {
        var diff = touchStartX - touchEndX;
        var threshold = 50;

        if (Math.abs(diff) < threshold) return;

        if (diff > 0) {
            if (currentPage < totalPages) {
                goToPage(currentPage + 1, 'next');
            }
        } else {
            if (currentPage > 1) {
                goToPage(currentPage - 1, 'prev');
            }
        }
    }

    // ===== URL Hash =====
    function getPageFromHash() {
        var hash = window.location.hash;
        if (hash) {
            var match = hash.match(/page=(\d+)/);
            if (match) {
                var page = parseInt(match[1]);
                if (page >= 1 && page <= totalPages) return page;
            }
        }
        return null;
    }

    function updateHash(pageNum) {
        if (window.history.replaceState) {
            window.history.replaceState(null, '', '#page=' + pageNum);
        } else {
            window.location.hash = 'page=' + pageNum;
        }
    }

    window.addEventListener('hashchange', function () {
        var page = getPageFromHash();
        if (page && page !== currentPage) {
            goToPage(page);
        }
    });

    // ===== Utility =====
    function escapeHtml(str) {
        if (!str) return '';
        var div = document.createElement('div');
        div.appendChild(document.createTextNode(str));
        return div.innerHTML;
    }

    function escapeAttr(str) {
        if (!str) return '';
        return str.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }
});
