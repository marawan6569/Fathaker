/**
 * Shared Mutashabihat Modal Logic
 * Used by Search page and Mushaf page
 */

const MutashabihatModal = (function () {
    // Elements
    let modal, overlay, closeBtn, body, title;

    function init() {
        modal = document.getElementById('mutashabihat-modal');
        overlay = document.getElementById('mutashabihat-overlay');
        closeBtn = document.getElementById('mutashabihat-close');
        body = document.getElementById('mutashabihat-body');
        title = document.getElementById('mutashabihat-title');

        if (!modal) return; // Modal HTML not present

        // Event listeners
        if (closeBtn) closeBtn.addEventListener('click', close);
        if (overlay) overlay.addEventListener('click', close);
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && modal.classList.contains('open')) {
                close();
            }
        });
    }

    function open(versePk) {
        if (!modal) return;

        if (title) title.textContent = 'متشابهات الآية ' + versePk;
        if (body) body.innerHTML = '<div class="mutashabihat-loading"><div class="spinner"></div><p>جاري التحميل...</p></div>';

        modal.classList.add('open');
        document.body.style.overflow = 'hidden';

        fetch('/verses/api/mutashabihat/by-ayah/?ayah=' + encodeURIComponent(versePk))
            .then(function (res) {
                if (!res.ok) throw new Error('خطأ في الاتصال');
                return res.json();
            })
            .then(function (phrases) {
                render(phrases, versePk);
            })
            .catch(function (err) {
                if (body) body.innerHTML = '<div class="mutashabihat-empty"><i class="fas fa-exclamation-triangle"></i><p>' + err.message + '</p></div>';
            });
    }

    function openPhrase(phraseId) {
        if (!modal) return;

        if (title) title.textContent = 'تفاصيل المتشابهة';
        if (body) body.innerHTML = '<div class="mutashabihat-loading"><div class="spinner"></div><p>جاري التحميل...</p></div>';

        modal.classList.add('open');
        document.body.style.overflow = 'hidden';

        fetch('/verses/api/mutashabihat/phrase/' + phraseId + '/')
            .then(function (res) {
                if (!res.ok) throw new Error('خطأ في الاتصال');
                return res.json();
            })
            .then(function (phrase) {
                // Determine source verse PK for highlighting context? 
                // For phrase view, maybe we don't need to highlight "Current Verse" specially, or pass null.
                render([phrase], null);
            })
            .catch(function (err) {
                if (body) body.innerHTML = '<div class="mutashabihat-empty"><i class="fas fa-exclamation-triangle"></i><p>' + err.message + '</p></div>';
            });
    }

    function close() {
        if (!modal) return;
        modal.classList.remove('open');
        document.body.style.overflow = '';
    }

    function highlightWords(verseText, wordFrom, wordTo) {
        var words = verseText.split(' ');
        var result = '';

        // We want to group the words from wordFrom to wordTo into one block
        // indices are 1-based

        var inHighlight = false;

        for (var i = 0; i < words.length; i++) {
            var wordNum = i + 1;

            // Start of highlight
            if (wordNum === wordFrom) {
                result += '<mark>';
                inHighlight = true;
            }

            result += escapeHtml(words[i]);

            // End of highlight
            if (wordNum === wordTo) {
                result += '</mark>';
                inHighlight = false;
            }

            // Add space if not last word
            if (i < words.length - 1) {
                result += ' ';
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

    function render(phrases, currentVersePk) {
        if (!body) return;

        if (!phrases || phrases.length === 0) {
            body.innerHTML = '<div class="mutashabihat-empty"><i class="fas fa-check-circle"></i><p>لا توجد متشابهات لهذه الآية</p></div>';
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

        body.innerHTML = html;
    }

    return {
        init: init,
        open: open,
        openPhrase: openPhrase
    };
})();
