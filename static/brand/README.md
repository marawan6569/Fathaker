# Fathaker design system

The shared brand layer is loaded after the existing page styles in `templates/base/base.html`. Existing Django routes, API contracts, audio logic, radio filtering and Quran content remain in their original modules.

- `tokens.css`: light/dark semantic colors, spacing, radii and locally hosted fonts.
- `design-tokens.json`: matching design-tool reference. Keep it synchronized when changing foundations.
- `system.css`: shared navigation, form controls, cards, players, dialogs and reading surfaces; responsive layouts and reduced-motion support.
- `theme.js`: theme initialization before first paint, accessible appearance toggle, persistence and cross-tab synchronization. System preference is used until a user explicitly selects a theme. Storage failure does not prevent switching. Also supplies a branded fallback for failed radio artwork.
- `logo-*.svg` and `favicon-*.svg`: editable vector assets for each appearance.
- `fonts/`: Noto Sans Arabic for interface text and Amiri Quran for Quran text, with their OFL licenses.

The three primary routes use a shared `primary_links.html` include, rendered in the desktop header and mobile bottom navigation. Additional database-managed links remain available in the header menu; footer links are preserved.

Use semantic variables rather than new color literals. Quran text must retain its own font, normal letter spacing and generous line height. Do not modify verse strings to achieve a visual effect.

Verification: Django system checks and 18 existing tests pass. Browser checks cover all three pages in both themes, phone and desktop layouts, six search modes, radio filtering, player controls, Mushaf navigation, similar-verse dialogs, theme persistence and horizontal overflow at 320/390/768/1440px. Media playback was simulated for UI testing; external live-stream availability was not certified.
