# Production Django custom-domain integration — 2026-11-17

## Actual serving state

- Application commit: `57c17d2452670ef5987e7216bad72cbff0b1d9bb`.
- Serving revision: `fathaker-domains-57c17d2`, Ready, 100% traffic.
- Immutable image:
  `us-east1-docker.pkg.dev/fathaker-quran/fathaker/web@sha256:73444c53c707d656664634c0d8fe36f2f2aa4273068ced08c452be2dea0675af`.
- https://fathaker.com serves the application. Existing https://www.fathaker.com
  redirect to the apex is preserved. Firebase and direct run.app remain accessible.

The owner had already connected/fixed the production domains before this task.
No DNS, Hostinger configuration, Firebase resources or Hosting releases were
changed here. This is the final Django host-integration update, not a data sync.

## Focused change

FIREBASE_HOSTS now includes the two Firebase-managed domains plus `fathaker.com`
and `www.fathaker.com`. Middleware still accepts only exact forwarded names also
present in ALLOWED_HOSTS. No wildcard, arbitrary suffix, comma-separated host,
URL-valued host or global forwarded-host trust was added. The existing header
precedence and cache policy are unchanged.

Both production domains were already present in the live ALLOWEDHOSTS and exact
HTTPS TRUSTEDORIGINS values. Every existing environment entry was preserved;
no environment edit was necessary. Before deployment, production og:url referred
to run.app; after deployment it uses the public hostname. The existing www→apex
redirect means www visitors correctly receive apex URLs rather than a separate
www page. No new forced redirect or canonicalization policy was introduced.

## Tests, CI and build

55 tests passed locally on SQLite and disposable PostgreSQL 16. The six new tests
cover both forwarded-host headers, both production domains, absolute/OG/share URLs,
redirects, exact allowlist/ALLOWED_HOSTS enforcement, unauthorized actual hosts,
Secure/HttpOnly/SameSite=Lax host-only __session cookies, session-backed CSRF,
untrusted-Origin rejection, synthetic authenticated login/logout and protected
admin access. Existing ORM/cache/image/upload/Arabic/Unicode regressions pass.
No model or migration changes; migration drift, static collection, dependency and
whitespace checks passed. Tests never connected to production Neon.

Application GitHub Actions run `44167152088` passed both database jobs and build.
Cloud Build `884c5d31-f398-4899-b09f-8e6ff64e9a68` succeeded with linux/amd64 and
in-image tests, from the exact committed archive verified by SHA-256:
`8c4affc5134c6d82e8c1b25c4c75d643b17b45f9bc5460c12b570d2fdc75128a`.
The two pre-existing uncommitted reconciliation reports were excluded from commit
and build input. No local .env, SQLite files, credentials or backups were uploaded.
Temporary `fathaker-build-domains` identity and its repository Writer/project Log
Writer/Service Usage Consumer grants were removed after build success.

## Live HTTPS acceptance

24 controlled HTTP checks plus fresh Chrome sessions verified:

- Apex/www homepage redirects, radio listing, verse/mushaf APIs, Firebase/run.app.
- Correct HTTPS og:url on each actual final host; www lands on the existing apex.
- 163 radio cards, visible 128px WebP decoding, no browser JavaScript errors.
- Public WebP thumbnail/artwork reads, radio CSS/JS and both Arabic font files.
- Unicode radio route OPTIONS returned 200. Counter-changing detail GET and like
  requests were deliberately unnecessary; detail/social URL handling is regression
  tested locally, including preservation of original image URLs.
- Production admin login page returned 200; __session flags were Secure, HttpOnly,
  SameSite=Lax. Missing CSRF was rejected 403. A valid session-backed CSRF token with
  the real apex Origin reached blank-form validation (200). No real password or
  authenticated production credentials were requested or handled.
- Anonymous bounded-range API returned s-maxage=300 with MISS→HIT→HIT. Session-bearing
  HTML remains private/no-store. No cache policy, media or audio URL changes.
- GA4 script loaded with `G-6NHQ4PT7XH` (200), and natural page-view collection
  requests to google-analytics.com/g/collect using that measurement ID returned
  204 for visits starting at either production hostname. No client/session IDs
  are recorded in this report. This verifies collection transport, not account-side
  Realtime ingestion, data filters, reporting latency or consent configuration.

Normal anonymous CSRF sessions can be created by these ordinary page checks.
There were no direct production DB writes, content edits, synchronization, media
writes, schema changes or migration commands. No radio counters were deliberately
incremented. Sampled new-revision logs had no unexpected application errors,
worker timeouts or memory-limit failures. This was functional checking, not load.

## Configuration preservation and rollback

Runtime spec comparison found **only the image changed**. Exact environment,
secret references, database/GCS settings, runtime service account, port, probes,
1 vCPU/512 MiB, concurrency 4, timeout 60s, CPU throttling, disabled startup boost,
min 0/max 2, request billing and PUBLIC_API_CACHE_TTL=300 are preserved.
Firebase's existing unpinned rewrite follows service traffic as before.

Previous serving revision `fathaker-cdn-restored-10b7b0b` remains Ready, with image
`sha256:efa426efec4fed3747d0215739c296f8e8e1f5bec8b4a9a9c711203faa4ceb16`.
Rollback, if required, does not touch data or media:

```sh
gcloud run services update-traffic fathaker --project=fathaker-quran \
  --region=us-east1 --to-revisions=fathaker-cdn-restored-10b7b0b=100
```

That rollback restores the previous custom-host absolute-URL limitation. No live
traffic rollback was needed for this small allowlist change.

## Readiness and remaining manual checks

**Technical GO for this Django custom-domain integration.** Public HTTPS, host
handling, API/cache/image behavior and GA4 transport passed. Owner-confirmed earlier
Firebase Admin acceptance remains valid history; it is not relabeled as successful
production-custom-domain authentication.

Manual production checks: log in and log out at https://fathaker.com/admin/login/,
confirm protected admin access and normal session behavior, and observe a visit in
GA4 Realtime for measurement ID G-6NHQ4PT7XH. No password should be shared. www
redirects to apex, so a separate www session is not expected in the current routing.

Final data reconciliation is not performed/certified by this change. The prior
local reconciliation reports remain separate. Legacy verse-audio remediation is
owner-accepted/deferred, not a launch blocker for this task. DNS, Hostinger, old
hosting, Firebase resources, production content/media and PR merge status were not
changed by this deployment.
