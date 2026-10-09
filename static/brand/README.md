# Fathaker design system

The shared brand layer is loaded after the existing page styles in `templates/base/base.html`. Existing Django routes, API contracts, audio logic, radio filtering and Quran content remain in their original modules.

- `tokens.css`: light/dark semantic colors, spacing, radii and locally hosted fonts.
- `design-tokens.json`: matching design-tool reference. Keep it synchronized when changing foundations.
- `system.css`: shared navigation, form controls, cards, players, dialogs and reading surfaces; responsive layouts and reduced-motion support.
- `controls.css`: the rebuilt Figma components (`ds-button`, `ds-icon-button`, `ds-chip`, `ds-field`, `station-card`, `ds-result`, `ds-player`) and composed control layouts. Radio/search templates and render functions use this markup, rather than only recoloring legacy controls.
- `icons.css` and `icons/`: local outlined vectors using the geometry saved with the Figma components. Legacy icon class aliases preserve existing play/pause state updates.
- `theme.js`: theme initialization before first paint, accessible appearance toggle, persistence and cross-tab synchronization. System preference is used until a user explicitly selects a theme. Storage failure does not prevent switching. Also supplies a branded fallback for failed radio artwork.
- `logo-*.svg` and `favicon-*.svg`: editable vector assets for each appearance.
- `fonts/`: Noto Sans Arabic for interface text and Amiri Quran for Quran text, with their OFL licenses.

The three primary routes use a shared `primary_links.html` include, rendered in the desktop header and mobile bottom navigation. Additional database-managed links remain available in the header menu; footer links are preserved.

Use semantic variables rather than new color literals. Quran text must retain its own font, normal letter spacing and generous line height. Do not modify verse strings to achieve a visual effect.

## Control behavior

- Radio: three primary filter controls, an expandable category menu, compact sort select, all matching stations displayed together, station identity/actions layout and a floating compact player. Station artwork is lazy-loaded with an icon fallback; favorite hearts are filled. Favorites uses the existing liked-radio list. The category label reflects the actual data; no reader-only category or listening-count metric is invented.
- Search: query first, three text matching options, an advanced disclosure for surah/page/range, six-result batches, plain verse references, and footer actions for similar verses and opening the verse page in the Mushaf.
- Reader: compact surah/page/juz controls, secondary settings menu, save/restore position in browser storage, surah listening, and previous/next controls below the reading surface. The surah action starts at its first verse and stops at its end.

The original Figma file remains `8z2rETk2TMMVpTgC06ZkVd`. This correction used the saved source definitions that created its components and screens because fresh Figma extraction was blocked by the Starter-plan MCP limit.

Verification: Django system checks and 18 existing tests pass. Browser checks cover all three pages in both themes, phone and desktop layouts, six search modes, radio filtering, player controls, Mushaf navigation, similar-verse dialogs, theme persistence and horizontal overflow at 320/390/768/1440px. Media playback was simulated for UI testing; external live-stream availability was not certified.
