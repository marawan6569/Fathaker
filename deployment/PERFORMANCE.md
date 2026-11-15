# ORM performance optimization — 2026-11-14

Baseline: migration branch `caa421a` (same application as deployed `28f8583`).

## Changes and causes

- Radio listing already prefetched tags, but template `tags.names()` performed
  a new values-list query per radio. Iterate `tags.all()` and use `tag.name`.
- All VerseSerializer endpoints now share a queryset joining surah and prefetching
  audio. Previously each serialized verse issued two extra queries.
- PhraseSerializer loads nested source surah/audio and occurrence verse/surah/audio
  in four queries. The old prefetch stopped before surah and audio, causing nested
  N+1 queries. Removed the shadowed, unused phrase detail class.
- Mushaf occurrence/phrase loading uses a joined Prefetch, removing one query.
- Serializer fields, filters, search operators, Unicode routes, counters and schema
  are unchanged. No caching, data migrations, or infrastructure changes.

## Reproducible isolated measurements

Python 3.12.3, pinned dependencies, SQLite and disposable PostgreSQL 16.15.
Synthetic fixture: 163 radios with two tags each, 200 verses over two surahs,
597 audio records, 30 phrases and 600 occurrences. Includes single-result, empty,
missing, and large-result requests. Three request samples per endpoint; medians
below. SQL duration measures cursor execute calls (including local driver latency,
not all result fetching). Response duration covers Django test-client request,
serialization and rendering; excludes HTTP network and browser asset downloads.
No production data was used by tests. PostgreSQL tests ran sequentially.

| Database | Endpoint | Queries before → after | SQL ms before → after | Response ms before → after |
| --- | --- | --- | --- | --- |
| sqlite | /verses/api/mushaf-page/ | 4 → 3 | 0.22 → 0.1 | 13.43 → 12.17 |
| sqlite | /verses/api/mutashabihat/search/ | 713 → 4 | 6.24 → 0.6 | 125.52 → 63.09 |
| sqlite | /radio/ | 169 → 6 | 1.94 → 0.11 | 58.55 → 27.68 |
| sqlite | /verses/api/search/ | 401 → 2 | 3.32 → 0.19 | 63.41 → 9.32 |
| pg | /verses/api/mushaf-page/ | 4 → 3 | 1.43 → 2.03 | 11.83 → 14.51 |
| pg | /verses/api/mutashabihat/search/ | 713 → 4 | 80.34 → 3.15 | 229.53 → 42.97 |
| pg | /radio/ | 169 → 6 | 29.28 → 1.3 | 95.8 → 29.44 |
| pg | /verses/api/search/ | 401 → 2 | 95.21 → 1.15 | 225.44 → 10.16 |

Run `PERFORMANCE_REPORT=1 python manage.py test verses.test_performance --noinput`
with explicit local database settings. Use `DATABASE_URL='' SQLITE_PATH=:memory:`
for SQLite, or a disposable local PostgreSQL URL. Never use Neon for tests.
`PERFORMANCE_BASELINE=1` disables budgets only for benchmarking the old checkout.

All JSON payload hashes match after canonicalizing unordered collections. These
APIs have no model/query ordering for verse/audio/phrase collections: PostgreSQL
can return different array order after a join/prefetch. Verse results now explicitly follow Quran number and serialized audio follows
primary key, stabilizing the UI’s range endpoints and first-recitation selection
against PostgreSQL join-plan changes. Previously those orders were incidental. Radio rank and mushaf verse order are explicitly asserted; all audio and
phrase fields/relationships are compared. Radio HTML matches on SQLite after
removing random CSRF tokens; PostgreSQL tag array order can differ, while tag
membership and escaping are preserved. Mushaf's first audio selection is unchanged.
The small mushaf timing increase is local measurement noise/extra joined columns;
its query count improves, but no latency improvement is claimed for that sample.

## Validation

35 tests pass on both databases, including new bounded-query tests for all verse,
phrase and mushaf endpoints, Arabic searches with/without tashkeel, empty audio,
radio ordering/tag escaping, and existing Unicode route, views/likes, authentication,
CSRF and storage tests. Dependency consistency, system checks, migration drift,
static collection and diff whitespace checks pass. No schema migration is needed.

## Initial deployment blocker (resolved below)

Authenticated gcloud is available at `~/google-cloud-sdk/bin/gcloud`.
The system Docker socket denies this user access; rootless Docker also fails because
`newuidmap` is missing. Cloud Build is not enabled, and no new build service or
resources were provisioned. Deployment requires a working Docker builder (or an
already approved alternative). Cloud Run remains `fathaker-upload-28f8583`, with
its original image, resource limits and rollback revision intact. DNS, old hosting,
Firebase, Neon data and original GCS media remain untouched.

After CI passes and a builder is available, build from the committed Git archive,
push to the existing registry, deploy by immutable digest to the existing service,
retain the previous revision, and repeat HTTP latency/payload checks. Do not run
migrations or tests against Neon. Complete this validation before image optimization
and subsequent hosting/CDN work; no public domain cutover yet.

## Read-only Neon measurements

Actual production content was queried inside an explicit `SET TRANSACTION READ ONLY`
transaction, verified by `SHOW transaction_read_only`, with a 15-second per-statement
limit. Secret Manager supplied the URL only in process memory. No test runner,
migrations, writes, or fixtures were used against Neon. One sample per endpoint,
from this development machine through the pooled TLS connection; these include WAN
latency and are **not Cloud Run HTTP latency**. JSON semantic hashes match baseline.

| Endpoint | Queries before → after | SQL ms before → after | Django response ms before → after |
| --- | --- | --- | --- |
| Radio | 169 → 6 | 37339.17 → 1389.14 | 37639.19 → 1514.86 |
| Search `الرحمن` (48 verses) | 97 → 2 | 18548.05 → 331.64 | 18626.80 → 342.20 |
| Mutashabihat search `الرحمن` | 343 → 4 | 76060.11 → 892.43 | 76357.35 → 921.05 |
| Mushaf page 1 | 4 → 3 | 787.67 → 452.58 | 795.75 → 457.35 |

The optimized mutashabihat search used 4 queries / 892.43 ms cursor time /
921.05 ms response; mushaf page 1 used 3 / 452.58 ms / 457.35 ms.

Read-only EXPLAIN ANALYZE of the search predicate returned 48/6236 rows in
11.779 ms, a sequential scan with 334 shared buffer hits. The expensive part was
repeated network round trips, so no speculative index or PostgreSQL extension was
added. Existing unique/FK indexes cover identifiers and relationships. Broad
substring scans and large JSON payload serialization remain worth measuring on
Cloud Run; full-corpus response memory/latency is not bounded by these query budgets.

## Cloud Run deployment and HTTPS acceptance — 2026-11-14

**Deployed application:** `abf821162c2917fb3e154943ad2a8795fd87487b`.
**Serving revision:** `fathaker-orm-abf8211`, Ready, 100% traffic.
**Immutable image:**
`us-east1-docker.pkg.dev/fathaker-quran/fathaker/web@sha256:a3d1ababc4d39683aa62276988de303b0a9bc8de46027fc82f4b0ad7b20daa19`.

### Build and configuration

One Cloud Build default-pool `E2_STANDARD_2` build in `us-east1`:
`1fcebe6e-d5c0-473a-b48c-351e3b47798d`, SUCCESS, approximately 57 seconds.
The Cloud Build API was enabled. The reviewed public commit was fetched by exact
SHA, exported with `git archive`, and compared against the local archive SHA-256:
`392ce7416b3a0bccfcae5fc34f8753aad7afaaccd18326e7c89a3623d7d0d690`.
The existing Dockerfile built with `--platform=linux/amd64`; all 35 SQLite tests
passed inside the resulting image before push. Target-commit GitHub Actions also
passed SQLite, PostgreSQL 17, fixture rehearsal and Docker build.

No working-directory files or local credentials were uploaded. No source bucket,
private worker pool, trigger, service-account keys, or permanent build identity was
created. Temporary `fathaker-build-abf8211` had only repository-scoped Artifact
Registry Writer, project Log Writer and Service Usage Consumer; all three bindings
were removed and the identity deleted after success. The broad existing Compute
Editor identity was not used or changed. Cloud Build's managed service agent and
API remain enabled; no recurring build workload was configured.

Pricing checked: default-pool e2-standard-2 qualifies for 2,500 free minutes/month
per billing account, then $0.006/minute. Remaining account-wide allowance could not
be verified. The 10-minute timeout bounded build compute at $0.06 before free
allowance; actual ~57-second compute is approximately $0.0057 if fully billed,
excluding ordinary registry/logging/network charges. See
[Cloud Build pricing](https://cloud.google.com/build/pricing).

The deployed runtime spec was compared against the saved old spec: only image
changed. CPU 1, memory 512 MiB, min 0, max 2, concurrency 4, timeout 60s, port 8080,
request billing/CPU throttling, disabled startup boost, runtime identity, environment,
GCS bucket, and both version-1 Secret Manager references are preserved.

### Real HTTPS comparison

Sequential requests from this machine to the actual service URL; two samples per
endpoint and revision, no concurrent load test. Times below are medians, except
radio uses the second request to exclude initial warm-up. All requests returned
200. Client time includes network and body transfer. Server time is Cloud Run
request-log `httpRequest.latency`, not pure SQL/application CPU time. There was no
Server-Timing response header. Benchmark markers correlate requests to revisions.

| Endpoint | Client seconds before → after | Cloud Run seconds before → after | Response bytes after |
| --- | --- | --- | --- |
| radio | 3.474 → 0.772 | 3.078 → 0.360 | 140,200 |
| search | 2.113 → 0.513 | 1.858 → 0.259 | 40,499 |
| broad | 59.468 → 1.673 | 58.477 → 0.663 | 1,841,679 |
| phrases | 6.109 → 0.734 | 5.653 → 0.295 | 179,445 |
| mushaf1 | 0.435 → 0.370 | 0.198 → 0.183 | 2,620 |
| mushaf604 | 0.461 → 0.464 | 0.199 → 0.184 | 5,248 |
| surah | 0.613 → 0.386 | 0.368 → 0.167 | 4,444 |
| verse | 0.463 → 0.380 | 0.185 → 0.163 | 624 |
| range | 1.013 → 0.444 | 0.806 → 0.173 | 14,540 |

Search used `الرحمن` (48 verses), broad search `الله`, mutashabihat `الرحمن`;
mushaf pages 1/604, surah 1, verse 1:1, and range 1–20. Before/after canonical JSON
hashes match for every paired API response. All 163 radio records match, including
rank, tag membership, streams, images, descriptions, Unicode slugs and counters.
Array-order changes are those documented above; radio tags were compared as sets.

Old revision's first radio request coincided with an AUTOSCALING cold start:
12.274s client / 11.204s Cloud Run. New revision started during deployment at
20:35:21–24 UTC; its first measured request at 20:35:48 was 5.491s / 4.824s.
That is first-request warm-up after deployment, **not a verified scale-from-zero
cold-start measurement**. Subsequent warm radio was 0.772s / 0.360s. A fresh cold
start of the optimized revision remains a future observation; no artificial
configuration changes or idle waiting were used to force one.

Large optimized requests, one sample each:

- All 6,236 verses / 18,708 audio links: 5,374,218 bytes, 3.490s client,
  2.474s Cloud Run; Quran-number ordering and relationship counts verified.
- Mutashabihat search `ا`: 4,845,937 bytes, 2.863s client, 1.526s Cloud Run.

Both returned HTTP 200 far below 60 seconds. This validates sequential requests,
not four simultaneous full-corpus requests or worst-case sustained memory.

### Regression smoke checks and limits

Passed Arabic search with/without tashkeel, all paired Quran/phrase/mushaf APIs,
radio contents and an external radio stream (HTTP 200, audio/mpeg sample), eight
static assets, both Arabic font files, and two original GCS image reads. Unicode
radio routing passed OPTIONS without incrementing views; detail GET/likes were
not exercised. Admin login page supplied a CSRF token and secure session cookie;
a missing-CSRF POST correctly returned 403. No credentials were available for a
new authenticated sign-in, so that was not claimed. Normal anonymous CSRF sessions
were created; no content, counters, users, migrations or imported data were changed.

One existing verse-audio URL at `cdn.alquran.cloud` failed DNS resolution from this
machine. API audio URLs match baseline exactly. External verse-audio playback
therefore remains unverified and needs an independent browser/network check.
No original GCS objects were written or deleted.

Logs showed no application errors, worker timeouts or memory-limit terminations
in the sampled new-revision window; the intentional CSRF rejection is expected.
Cloud Monitoring one-minute memory-usage samples for the new revision through
20:38 UTC ranged from 54.7 to 120.9 MiB; separate utilization samples reached
25.4%. The previous revision sampled up to 148.3 MiB / 29.0%. These are sampled
distribution means, not exact instantaneous peaks, and do not establish safety
for four simultaneous large responses. No sampled value approached 512 MiB.

### Rollback and next phase

Previous revision `fathaker-upload-28f8583` and image
`sha256:ad435b8148c576fd9223bb6c11e6c36ac8bf2dc194b76ae18f8197a578041887`
remain available. Roll back traffic without touching Neon:

```sh
gcloud run services update-traffic fathaker --project=fathaker-quran \
  --region=us-east1 --to-revisions=fathaker-upload-28f8583=100
```

Remaining costs are response transfer/serialization, initial-request warm-up,
external audio availability and large original radio images (sample images exceed
2 MB each). ORM readiness is demonstrated for the controlled HTTPS sample. WebP
optimization can be planned next with original backups preserved; no conversion,
Firebase setup, DNS changes, old-host changes, Redis, or PR merge occurred here.
Recheck external audio and cold-start behavior before public cutover.

## Radio image follow-up — 2026-11-15

Radio WebP optimization is deployed as `fathaker-images-bc3c91b` (application
`bc3c91b`). Chrome complete-list image transfers improved from 310.53 MB to
413.53 KB; the 154 originals and all database image references are preserved.
See [RADIO_IMAGES.md](RADIO_IMAGES.md) for exact bytes, verified image digest,
visual comparisons, tests, rollback verification and final-sync instructions.
The ORM query loading and Cloud Run resource limits are unchanged.
