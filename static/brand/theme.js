/* Load before styles to prevent a flash of the wrong theme. */
(() => {
    'use strict';
    const key = 'fathaker-theme';
    const root = document.documentElement;
    const preference = window.matchMedia('(prefers-color-scheme: dark)');
    let saved;
    try { saved = localStorage.getItem(key); } catch (_) { /* Private storage may be unavailable. */ }
    let explicit = saved === 'light' || saved === 'dark';
    function apply(theme) {
        root.dataset.theme = theme;
        document.querySelectorAll('.theme-toggle').forEach(button => {
            button.setAttribute('aria-pressed', String(theme === 'dark'));
            button.setAttribute('aria-label', theme === 'dark' ? 'تفعيل الوضع الفاتح' : 'تفعيل الوضع الداكن');
        });
        const meta = document.querySelector('meta[name="theme-color"]');
        if (meta) meta.content = theme === 'dark' ? '#0E201D' : '#F7F8F5';
        const favicon = document.querySelector('link[rel="icon"]');
        if (favicon) favicon.href = favicon.href.replace(/favicon-(light|dark)\.svg/, `favicon-${theme}.svg`);
    }
    apply(explicit ? saved : preference.matches ? 'dark' : 'light');
    document.addEventListener('error', event => {
        const image = event.target;
        if (!(image instanceof HTMLImageElement) || !image.matches('.card-img-wrapper img,.player-art,.fullscreen-art,.detail-art')) return;
        const fallback = document.body?.dataset.radioFallback;
        if (fallback && image.getAttribute('src') !== fallback) image.src = fallback;
    }, true);
    document.addEventListener('DOMContentLoaded', () => {
        apply(root.dataset.theme);
        document.querySelectorAll('.theme-toggle').forEach(button => button.addEventListener('click', () => {
            const next = root.dataset.theme === 'dark' ? 'light' : 'dark';
            explicit = true;
            try { localStorage.setItem(key, next); } catch (_) { /* Still switch in this tab. */ }
            apply(next);
        }));
    });
    preference.addEventListener('change', event => { if (!explicit) apply(event.matches ? 'dark' : 'light'); });
    window.addEventListener('storage', event => {
        if (event.key !== key) return;
        explicit = event.newValue === 'light' || event.newValue === 'dark';
        apply(explicit ? event.newValue : preference.matches ? 'dark' : 'light');
    });
})();
