# Radio WebP optimization

## Inventory and design

2026-11-15 baseline: 154 PNG objects, 310,443,753 bytes, all 1254×1254,
no transparent pixels, 134 unique SHA-256 contents. Per-file names, keys, dimensions,
format, transparency, bytes, checksums and generations are in
[original-inventory.json](image-reports/original-inventory.json).

Listing cards display at 56px and use 128px thumbnails (sufficient for 2× displays).
Detail hero, background, bottom player, fullscreen player and MediaSession use
768px artwork. JavaScript `img` remains artwork; `thumbnail` is additive.
Open Graph/Twitter retain original PNG URLs. Database fields and original public
URLs are unchanged. Manifest lookup loads once per process and uses storage URL
construction without HEAD/exists requests or database queries. Unknown uploads,
missing/malformed manifests and invalid entries fall back to the original URL;
empty image fields retain the static placeholder. Network-failed listing images
retain the existing icon fallback.

## Conversion and quality

Pillow 10.3.0: EXIF orientation applied, aspect ratio preserved, LANCZOS bounding-box
resize, never upscaled/cropped, RGB/RGBA according to actual transparency. New image
metadata is cleared. Compare WebP quality 84/method 6 against lossless and keep the
smaller candidate; all real candidates selected lossy. Alpha remains encoded.
Skip any result saving less than 5%, and skip animated input. Existing inventory
needed no skips. Synthetic transparency, small-size and repeatability tests pass.

Eight-image pilot includes smallest/largest originals, portraits, fine clothing
patterns and textured artwork. All originals have the same dimensions/transparency,
so those cases are tested synthetically. Visual inspection of
[pilot comparison](image-reports/pilot-comparison.jpg) and the
[768px comparison](image-reports/artwork-detail.jpg) found acceptable detail and
no destructive changes. Thumbnails intentionally discard details below card size.

| Variant | Bytes across 154 paths | Savings versus originals | Unique object bytes |
| --- | ---: | ---: | ---: |
| Thumbnail | 462,526 | 99.851% | 404,768 |
| Artwork | 7,421,458 | 97.609% | 6,473,238 |

There are 268 unique optimized objects, 6,878,006 additional bytes. Originals remain
in place and billable storage increases by that amount; transfer savings do not
mean original storage was removed. Thumbnail savings range 99.763% (`radio-057.png`)
to 99.896% (`radio-127.png`); artwork savings range 95.589% (`radio-165.png`) to
98.963% (`radio-127.png`). All 154 images benefit from both variants; originals
remain preferred for social previews, backups, regeneration and rollback.

## Safe generation and publication

Use an isolated workspace outside Git and put the authenticated gcloud on PATH:

```sh
python deployment/optimize_radio_images.py inventory --work /private/image-work
python deployment/optimize_radio_images.py generate --work /private/image-work --pilot 8
# Inspect pilot.json and local original/variant comparisons before continuing.
python deployment/optimize_radio_images.py generate --work /private/image-work
python deployment/optimize_radio_images.py publish --work /private/image-work
```

Only `publish` writes GCS, and only `radio/optimized/v1/<SHA256>-<kind>.webp`.
It uses `if_generation_match=0`; existing hashes must match exactly. Source reads
are generation-pinned. Before publishing, original generations/checksums must
still match. Content is `image/webp`, cache is
`public, max-age=31536000, immutable`. Every variant is decoded and dimensions
checked, GCS MD5/bytes checked, and its public HTTP response is verified by SHA-256
and decoding before atomically writing `radio/image_manifest.json`. Duplicate
content shares object keys. No bucket, background worker, scheduler or service is
created. Existing prior hashes are retained on regeneration, never deleted.

For final migration sync or later images: repeat inventory after originals have
been safely synchronized by the separately reviewed migration procedure. Compare
keys, SHA-256 and generations with the tracked inventory; regenerate/publish and
review the new manifest, then deploy it. New keys work immediately through original
fallback. If content is replaced under the SAME original key, regenerate the
manifest before cutover, since lookup deliberately makes no storage probes.
Do not change `Radio.image` or blindly overwrite originals using this script.

## Verification and deployment

40 tests pass on SQLite and disposable PostgreSQL 16, including existing admin
upload/CSRF tests, Unicode detail routes, fallback behavior, unchanged image values,
original social URLs, no-query lookup, query budgets and deterministic conversion.
No migrations. Browser baseline: all 154 image elements decoded, no JavaScript
errors; cache-disabled Chrome CDP measured 310,528,054 bytes across image responses
(includes response overhead). Browser resource timing alone reports zero for
cross-origin sizes without Timing-Allow-Origin, so CDP is used for transfer sizes.

All 268 unique WebP objects passed GCS metadata/checksum checks and public HTTP
200 byte-for-byte SHA-256/decode verification. The prefix inventory matches exactly,
with no prior optimized objects. The first verification attempt hit a transient
HTTP timeout and wrote no manifest; the idempotent retry verified all existing
objects without replacing any. Final bucket comparison verified all 154 original
generations, MD5 values and byte sizes unchanged. All 163 live radio slugs also
resolved locally without counter-changing requests.

## Deployed acceptance

Application commit `bc3c91b694feb61428e6e91d9549ce6c96625ec3`.
Serving revision: `fathaker-images-bc3c91b`, Ready, 100% traffic.
Immutable image:
`us-east1-docker.pkg.dev/fathaker-quran/fathaker/web@sha256:2e74d992983983fba936aae68e37972350d1e527bb700c0ce91680a97aa7146d`.

GitHub Actions run `43701378898` passed SQLite/PostgreSQL, fixture rehearsal,
static checks and Docker build. Cloud Build `14dd3450-fec2-436b-9eb5-54c678f2a50a`
succeeded in approximately 55 seconds using E2_STANDARD_2, a linux/amd64 build,
and all 40 in-image tests. Exact Git archive SHA-256:
`36dd7b1610c78d33a9f7e5d578966a06f988a07190b345a869991221befff6e3`.
The source was fetched by exact commit and archive hash checked in the builder.
No local .env, credentials, SQLite or private originals/backups were uploaded.
The existing Cloud Build API/default pool and registry were used. Temporary build
identity `fathaker-build-images` and all three narrow IAM grants were removed.
No triggers, worker pools, buckets, processing services or recurring jobs added.

Runtime spec comparison confirmed CPU 1, memory 512 MiB, min 0/max 2, concurrency 4,
60-second timeout, request billing, CPU throttling, disabled startup boost,
identity, environment, secrets and storage configuration preserved.

Real Chrome validation on run.app (1400×1000, 1× display, fresh context, cache
disabled, all lazy card images explicitly requested):

| Measurement | Original revision | WebP revision |
| --- | ---: | ---: |
| Decoded image elements | 154/154 | 154/154 |
| Actual image network requests | 154 | 134 |
| CDP encoded transfer including overhead | 310,528,054 bytes | 413,529 bytes |
| Decoded card size | 1254×1254 | 128×128 |
| JavaScript errors | 0 | 0 |

Actual listing transfer reduction: **99.867%**. Duplicate thumbnails share URLs,
which explains the difference from the 462,526-byte per-source total. These are
complete-list image transfers, not initial viewport or whole-page load timings.
See [browser comparison](image-reports/browser-comparison.jpg).

Bottom/fullscreen player, fullscreen background, detail image and detail background
used the verified artwork URLs; detail image decoded at 768×768 and returned 200.
Open Graph retained `radio/radio-004.png`. MediaSession used artwork without an
incorrect MIME/size declaration. Player UI was exercised with only audio.play()
stubbed in Chrome to avoid unattended playback; a separate actual radio stream
request returned 200/audio-mpeg with a 1024-byte sample. Quran verse/search/mushaf
API checks and admin login/session/CSRF availability passed. A missing-CSRF admin
POST returned 403 as expected. Existing mocked admin/GCS upload tests passed;
no new media or authenticated admin content was created in production.

One intentional detail GET added one normal view to the first radio (radio-004);
no like/rank requests were sent. `Radio.image` values were never written; no DB
migration/import/reset was run. No unexpected errors, worker timeouts or memory
limit errors were found in the sampled new-revision logs. This is a controlled
functional/image-loading check, not a load test or new authentication audit.

## Rollback verification and remaining migration steps

A controlled traffic rollback to `fathaker-orm-abf8211` was performed. Its live
listing returned 200 with 163 radio records and all 154 original PNG references,
without thumbnail metadata. The pre-deployment browser baseline had decoded all
154 originals. Traffic was then restored to `fathaker-images-bc3c91b` at 100%,
and WebP HTML was verified again. The previous revision and its immutable image
`sha256:a3d1ababc4d39683aa62276988de303b0a9bc8de46027fc82f4b0ad7b20daa19`
remain available. Rollback requires no database or bucket changes:

```sh
gcloud run services update-traffic fathaker --project=fathaker-quran \
  --region=us-east1 --to-revisions=fathaker-orm-abf8211=100
```

Ready for a separately authorized Firebase Hosting/CDN phase. Optimized assets
already have immutable browser-cache headers; dynamic API caching, Firebase proxy
behavior and DNS cutover still require their planned verification. Reconcile final
old-host content/media changes and regenerate this manifest before cutover. The
previously documented external verse-audio CDN issue remains separate from image
optimization. DNS, old hosting, Firebase and PR merge status are unchanged.
