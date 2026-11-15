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

Deployment verification will be recorded after CI completes.
