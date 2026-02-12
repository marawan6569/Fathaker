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

    var currentPage = 1;
    var totalPages = 604;
    var isLoading = false;
    var pageCache = {};

    // Surah first pages lookup (built from SURAHS data or fetched dynamically)
    var surahFirstPages = {};

    // Arabic numerals
    var arabicNumerals = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'];

    function toArabicNum(num) {
        return String(num).split('').map(function (d) {
            return arabicNumerals[parseInt(d)] || d;
        }).join('');
    }

    // ===== Initialization =====
    // Check URL hash for initial page
    var hashPage = getPageFromHash();
    if (hashPage) {
        currentPage = hashPage;
        pageInput.value = currentPage;
    }

    loadPage(currentPage);

    // ===== Page Loading =====
    function loadPage(pageNum, direction) {
        if (isLoading) return;
        pageNum = Math.max(1, Math.min(totalPages, pageNum));

        // Check cache
        if (pageCache[pageNum]) {
            renderPage(pageCache[pageNum], direction);
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
                renderPage(data, direction);
                isLoading = false;

                // Prefetch adjacent pages
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
    function renderPage(data, direction) {
        currentPage = data.page;
        pageInput.value = currentPage;

        // Update info badges
        juzLabel.textContent = 'الجزء ' + toArabicNum(data.juz);

        if (data.surahs_on_page && data.surahs_on_page.length > 0) {
            var surahNames = data.surahs_on_page.map(function (s) { return s.name; });
            surahLabel.textContent = surahNames.join(' - ');

            // Record first pages for surahs
            data.surahs_on_page.forEach(function (s) {
                if (!surahFirstPages[s.id]) {
                    surahFirstPages[s.id] = currentPage;
                }
            });
        }

        // Update URL hash
        updateHash(currentPage);

        // Build page HTML
        var html = '';
        var currentSurahId = null;

        for (var i = 0; i < data.verses.length; i++) {
            var v = data.verses[i];

            // Insert surah header if first verse of the surah
            if (v.is_first_in_surah) {
                // Close previous verse block if open
                if (currentSurahId !== null) {
                    html += '</div>'; // close previous .mushaf-verse-block
                }

                html += buildSurahHeader(v.surah_name, v.surah_id);
                currentSurahId = v.surah_id;

                // Open new verse block
                html += '<div class="mushaf-verse-block">';
            } else if (currentSurahId === null || currentSurahId !== v.surah_id) {
                // Page starts mid-surah, just open the verse block
                if (currentSurahId === null) {
                    html += '<div class="mushaf-verse-block">';
                }
                currentSurahId = v.surah_id;
            }

            // Verse text with ayah marker
            html += '<span class="mushaf-verse-text">' + escapeHtml(v.verse) + '</span>';

            // Sajda marker
            if (v.is_sajda) {
                html += '<span class="mushaf-sajda-marker">سجدة</span>';
            }

            // Ayah number ornament
            html += '<span class="mushaf-ayah-marker"><span>' + toArabicNum(v.number_in_surah) + '</span></span>';
        }

        // Close last verse block
        if (currentSurahId !== null) {
            html += '</div>';
        }

        pageContent.innerHTML = html;
        pageNumberEl.textContent = toArabicNum(currentPage);

        // Apply page turn animation
        hideLoading();
        pageContainer.style.display = 'flex';

        if (direction) {
            pageContainer.classList.remove('turning-next', 'turning-prev');
            // Force reflow
            void pageContainer.offsetWidth;
            pageContainer.classList.add(direction === 'next' ? 'turning-next' : 'turning-prev');
            setTimeout(function () {
                pageContainer.classList.remove('turning-next', 'turning-prev');
            }, 450);
        }
    }

    function buildSurahHeader(surahName, surahId) {
        var html = '<div class="mushaf-surah-header">';
        html += '<div class="mushaf-surah-name-banner">سُورَةُ ' + escapeHtml(surahName) + '</div>';
        html += '</div>';

        // Add Bismillah for all surahs except Al-Fatiha (1) and At-Tawbah (9)
        if (surahId !== 1 && surahId !== 9) {
            html += '<div class="mushaf-bismillah">بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ</div>';
        }

        return html;
    }

    // ===== Navigation =====
    function goToPage(pageNum, direction) {
        pageNum = Math.max(1, Math.min(totalPages, pageNum));
        if (pageNum === currentPage && pageCache[pageNum]) return;
        loadPage(pageNum, direction);
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

        // If we have the first page cached, use it
        if (surahFirstPages[surahId]) {
            goToPage(surahFirstPages[surahId]);
            surahJump.value = '';
            return;
        }

        // Otherwise, fetch from API to find the page
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
        // Don't navigate if user is typing in an input
        if (document.activeElement.tagName === 'INPUT' || document.activeElement.tagName === 'SELECT') return;

        if (e.key === 'ArrowRight') {
            // Right arrow = previous page (RTL: going back)
            e.preventDefault();
            if (currentPage > 1) {
                goToPage(currentPage - 1, 'prev');
            }
        } else if (e.key === 'ArrowLeft') {
            // Left arrow = next page (RTL: going forward)
            e.preventDefault();
            if (currentPage < totalPages) {
                goToPage(currentPage + 1, 'next');
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
            // Swipe left = next page
            if (currentPage < totalPages) {
                goToPage(currentPage + 1, 'next');
            }
        } else {
            // Swipe right = previous page
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

    // Handle browser back/forward
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
});
