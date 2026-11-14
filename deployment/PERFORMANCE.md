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

## Deployment

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

The optimized mutashabihat search used 4 queries / 892.43 ms cursor time /
921.05 ms response; mushaf page 1 used 3 / 452.58 ms / 457.35 ms.

Read-only EXPLAIN ANALYZE of the search predicate returned 48/6236 rows in
11.779 ms, a sequential scan with 334 shared buffer hits. The expensive part was
repeated network round trips, so no speculative index or PostgreSQL extension was
added. Existing unique/FK indexes cover identifiers and relationships. Broad
substring scans and large JSON payload serialization remain worth measuring on
Cloud Run; full-corpus response memory/latency is not bounded by these query budgets.
