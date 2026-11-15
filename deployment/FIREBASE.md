# Firebase Hosting and selective API CDN caching

## Hosting configuration

Project/site: `fathaker-quran` (the existing GCP project, not a new project).
Public URLs: https://fathaker-quran.web.app and
https://fathaker-quran.firebaseapp.com. No custom domain attached.

Hosting release `1794737564753000`, version `b75c6d61a4c0ce12` contains zero files
and a catch-all Cloud Run rewrite to `fathaker` in `us-east1`. No SPA fallback,
Cloud Functions, App Hosting or revision pinning. `public/` contains only ignored
`.gitkeep`; Django/WhiteNoise serves static files. The checked-in firebase.json
now names the actual site. With authenticated gcloud on PATH, the narrow REST
script `python deployment/firebase/deploy_hosting.py` can redeploy exactly this
configuration without Node, Firebase login tokens or service-account keys.

Added only the two Hosting domains to ALLOWEDHOSTS/TRUSTEDORIGINS, retaining all
existing values. Config-only revision `fathaker-firebase-hosts-bc3c91b` uses the
previous WebP image and provides a pre-caching rollback with Hosting hosts allowed.
All CPU, memory, scaling, concurrency, timeout, identity, secrets and GCS settings
are preserved. Direct run.app continues to work.

Firebase Management and Hosting APIs were explicitly enabled. `addFirebase` added
Firebase configuration to the existing project and provisioned its managed service
identities/supporting APIs (including Installations, Remote Config/Realtime,
Rules and Identity Toolkit). No Firebase databases, Analytics, Firebase Auth
providers, remote-config templates, new buckets or workload services were created.
No broad user-managed IAM grants were added for Hosting.

The project already had a linked Cloud Billing account. Firebase uses that account
and the Blaze plan; no new billing account/paid-plan purchase was made. Hosting
includes 10 GB storage and 360 MB/day transfer, then $0.026/GB storage and $0.15/GB
transfer at the checked public rates. Dynamic CDN hits still incur Hosting transfer
and do not make network traffic free. This release stores zero static bytes.
Existing project budget alerts remain relevant and are not spending caps.
References: [Firebase pricing](https://firebase.google.com/pricing),
[existing-project integration](https://firebase.google.com/docs/projects/use-firebase-with-existing-cloud-project).

## Proxy acceptance before enabling caching

Both Hosting hostnames and run.app returned correct homepage redirects, radio,
mushaf API and admin availability with private/no-store dynamic headers.
The primary Hosting domain also passed Quran search/mushaf HTML, representative
verse/surah/range/search/mutashabihat APIs, JavaScript and both Arabic fonts.
Chrome decoded all 154 WebP card images without JS errors, and exercised bottom/
fullscreen artwork, backgrounds and one Unicode detail route; social previews
still point to original GCS PNGs. Radio stream returned HTTP 200/audio-mpeg.

Session cookie observed: `__session`, Secure, HttpOnly, SameSite=Lax. A login POST
without CSRF was rejected 403. A session-backed valid-CSRF blank login submission
reached ordinary form validation (200) through Firebase with its real Origin.
No password was requested, logged or submitted. These prove proxy/session/CSRF
availability, not successful user authentication. Authenticated login/logout,
admin uploads and session messages need the user's manual acceptance at
https://fathaker-quran.web.app/admin/login/. Local tests also cover a real Django
login and CSRF-protected likes with Firebase-style cookie filtering, and mock GCS
upload persistence/collision handling. They do not replace live admin acceptance.
Two detail smoke requests (HTTP and browser) caused two normal view increments;
no likes/rank actions, content synchronization or original media writes occurred.
Normal anonymous admin/CSRF sessions were created.

Firebase adds its own HSTS for its managed domains. Direct Cloud Run retains the
existing one-hour HSTS; HTTPS forwarding produces HTTPS URLs. Initial inspection found Host rewritten
to the Run hostname in og:url/share URLs; the middleware restores only the two
exact Hosting names from x-fh-requested-host/X-Forwarded-Host when also present
in ALLOWED_HOSTS. Arbitrary forwarded hosts are ignored, avoiding global trust
of client-supplied forwarded-host values.
No redirect loop or SPA replacement was observed.

## Cache safety audit and policy

NoStoreMiddleware remains private by default, outside SessionMiddleware so it sees
response cookies. WhiteNoise remains outside it and handles public static assets
as before. GCS immutable WebP cache policy is unchanged.

| Anonymous JSON candidate | Bounds/parameters |
| --- | --- |
| Mushaf page API | No query, or one `page` from 1 to 604 |
| Verse detail API | No query; existing verse lookup |
| Surah verses API | Surah 1–114, no `q` or other query |
| Verse range API | Both ends 1–6236; at most 100 verses, reversed ranges preserved |
| Mutashabihat phrase detail | No query; existing phrase lookup |
| Mutashabihat by ayah | Exactly one syntactically valid `ayah=S…V…` |

Each candidate serializes only Quran/surah/audio/phrase data, without user or CSRF
fields, and performs no counter writes. Public headers additionally require:
GET/HEAD; status 200; application/json; non-streaming response no larger than 1 MiB;
no request Cookie or Authorization header; no authenticated user; no response
cookies/Set-Cookie; no attachment, `Vary: *`, or explicit private/no-store header.
All other dynamic responses retain `Cache-Control: private, no-store`.

Production activation is `PUBLIC_API_CACHE_TTL=300`; default 0 is disabled.
Allowed configuration range is 0–900 seconds. Public header:
`Cache-Control: public, max-age=0, s-maxage=300`.
Vary includes Cookie, Authorization and Accept, preserving existing values.
Browsers must revalidate while shared CDN caches may reuse for the short TTL.
Firebase also keys dynamic content on host, path, query string, content negotiation
and its special `__session` cookie. Only `__session` is forwarded to Cloud Run;
other cookies may be stripped by Hosting. Direct run.app conservatively rejects
public caching for any Cookie header.
Reference: [Hosting cache and cookie behavior](https://firebase.google.com/docs/hosting/manage-cache).

HTML, radio listing/detail counters, likes/rank actions, admin/login/logout,
session-bearing/authenticated/Authorization responses, every mutation, errors,
browsable API HTML, full-corpus listing, oversized responses and unknown or duplicate
query parameters are excluded. No response payloads or search semantics change.

Quran substring/prefix/suffix and mutashabihat searches remain uncached: high query
cardinality, potentially multi-megabyte responses and no measured real-user repeat
rate/hit-rate evidence justify adding them yet. Surah `q` searches are excluded too.

## Expiration, disable switch and rollback

Quran/audio/phrase edits become visible to anonymous cached consumers when their
entry expires (at most the configured TTL after fill). Session-bearing/admin
requests always reach the origin. Radio content and counters are never shared-
cached here. No purge service, Redis, scheduler or application data cache.

Set `PUBLIC_API_CACHE_TTL=0` on the service to disable new public API cache responses.
Already cached anonymous responses can survive for the remaining TTL; this is not
an immediate purge. Wait the TTL before claiming a globally empty cache. Changing
TTL does not retroactively shorten existing entries. For urgent origin rollback,
route to `fathaker-firebase-hosts-bc3c91b` (same safe pre-cache application plus
Hosting domains). Existing anonymous entries remain bounded by their prior TTL.
No rollback changes Neon or GCS. Firebase Hosting continues following service
traffic, since there is no revision tag pin.

## Deployed cache acceptance — 2026-11-15

Application commit `10b7b0b2c443220537f28f4072e17b301fbe46de`.
Final serving revision `fathaker-cdn-restored-10b7b0b`, 100% traffic, TTL 300.
Image: `us-east1-docker.pkg.dev/fathaker-quran/fathaker/web@sha256:efa426efec4fed3747d0215739c296f8e8e1f5bec8b4a9a9c711203faa4ceb16`.

Cloud Build `e3a44764-819b-4332-8ba1-4f5e1e269de8` succeeded using the existing
linux/amd64 process and a temporary narrowly scoped build identity. All build grants
and `fathaker-build-cdn` were removed afterward. Exact reviewed Git archive hash:
`4b8d5cc7ecc040cc5a602d3100989b9eef8ef11f94ede9b95923e7b99b902776`.
GitHub Actions `43703592486` passed both database jobs and Docker build.
All 49 tests passed on SQLite and disposable PostgreSQL 16. The five existing ORM
performance tests were additionally rerun on both databases with the production
middleware order and TTL 300 enabled; all query budgets and payload checks passed.
No migrations. Production database was not used by the test runner.

### Observed CDN reuse and correctness

Sanitized request/header/hash samples and matching origin request summaries are
in [CDN_EVIDENCE.json](firebase/CDN_EVIDENCE.json). No session tokens or request
Authorization values are included.

| Controlled range 4331–4333 sample | CDN | Client seconds |
| --- | --- | ---: |
| Initial | MISS | 0.572 |
| Repeat 1 | HIT | 0.106 |
| Repeat 2 | HIT | 0.106 |
| Repeat 3 | HIT | 0.084 |
| Repeat 4 | HIT | 0.093 |

All five bodies had identical SHA-256 and 2,162 bytes. Same edge identifier;
X-Cache-Hits increased 0→4. Matching Cloud Run logs contain exactly one origin
request for that five-request sample (0.158s origin latency). Thus four requests
were actually served without running Django: 80% origin-request reduction in this
controlled sample, not an estimate of production-wide hit rate. Median HIT latency
was 0.100s, versus 0.572s on the initial warm-origin MISS. Direct Cloud Run remains
functional and returned identical bytes for the other sampled range (4321–4323).

A separate first-request sample took 5.150s client / 4.660s origin and is treated as
initial warm-up, not steady-state latency or a verified scale-from-zero cold-start
benchmark. New connections sometimes reached different edge nodes and caused
additional misses; no global hit-rate claim is based on this small sample.

Pages 17/18 and 201/202 returned their correct, distinct verse data. Cache-key tests
include repeated page URLs; q searches returned distinct correct content and stayed
private. Mutashabihat phrase 4596 and by-ayah S2V23 passed. Phrase 1 was absent and
correctly returned an uncached 404; no API contract change was made to force it.

Two requests with a genuine anonymous __session from the admin CSRF form both
returned private/no-store and MISS, reaching the origin each time. Their JSON bytes
matched the public payload. An invalid Basic Authorization request returned private
403/MISS; POST returned private 405/MISS. Radio/admin HTML (including Set-Cookie),
search, and >100-verse ranges stayed private. HEAD returned correct headers without
a body. Real authenticated-user cache bypass is covered locally, but live user
authentication remains pending manual acceptance, as stated above.

### Expiry and disable verification

After 315.58 seconds from the first fill, the identical range URL returned MISS,
X-Cache-Hits 0 and the exact original payload. A new request appears in Cloud Run
logs at 10:29:12 UTC on `fathaker-cdn-restored-10b7b0b` (0.159s origin latency).
This is a real post-TTL refill observation; no data was edited to manufacture it.
It is not a claim to have inspected every CDN node or purged global caches.

The disable switch was exercised live: config revision
`fathaker-cdn-disabled-10b7b0b` with TTL 0 served a fresh bounded-range URL as 200,
private/no-store, MISS. Then TTL 300 was restored in a new config revision and
traffic returned to the final serving revision above. No rebuild or data changes
were required. The disabled revision remains an immediately available origin
rollback, preserving the forwarded-host fix:

```sh
gcloud run services update-traffic fathaker --project=fathaker-quran \
  --region=us-east1 --to-revisions=fathaker-cdn-disabled-10b7b0b=100
```

For a new TTL config update, remember that traffic is explicitly pinned. An env
update alone creates a revision but may not move traffic. Review the new revision,
then route traffic explicitly (or `--to-latest` immediately after the reviewed
update). Existing CDN entries still expire by their previous TTL. Original image
revision `fathaker-images-bc3c91b`, config-only Hosting revision and immutable
images are retained for application rollback.

### Cost, stability and outstanding acceptance

Final runtime comparison preserved 1 vCPU/512 MiB, min 0/max 2, concurrency 4,
60s timeout, request billing, runtime identity, all existing secrets and GCS config.
Only reviewed image, Hosting hosts/origins and TTL differ from the original setup.
No unexpected errors, worker timeouts or memory-limit failures were observed in
the sampled new-revision logs. This was sequential testing, not concurrent load.
Concurrent full-corpus memory and fresh scale-from-zero latency remain previous
risks to observe; public-cache eligibility does not change uncached API semantics.

Hosting Monitoring's delayed monthly_sent samples showed 752,911 bytes for
firebaseapp.com (10:13:59 UTC) and 3,468,615 bytes for web.app (10:18:59 UTC), about
4.22 MB combined. Those samples lag this validation and are not a complete bill.
The Hosting release has zero user static files; storage metric had no samples yet.
No unexpected recurring infrastructure was introduced, but Hosting egress beyond
its allowance is billable and the Blaze transfer limit is not a spending cap.
GCS images are downloaded directly and are outside Hosting's transfer counter.

No Neon provider activity metrics were available. Four avoided range requests
would avoid roughly eight ORM queries using the verified two-query loading plan;
that is an inference, not measured Neon telemetry. Most visitors who already have
an anonymous radio/admin CSRF session bypass this conservative CDN policy too;
real traffic data is needed before claiming broad cost savings or caching search.

Independent external verse-audio check: the stored cdn.alquran.cloud URL still
fails from this machine, and both Google and Cloudflare DNS-over-HTTPS return
NOERROR with no A/AAAA answers. Existing audio URLs were not rewritten. Radio
streaming works; resolve this external-audio issue before domain cutover.

Before cutover: obtain manual authenticated login/logout/upload/messages acceptance
on Hosting; reconcile old-host content/media under separate approval; regenerate
WebP manifest if needed; verify Firebase cookie behavior on the approved custom
hosts; extend the exact forwarded-host allowlist only when attaching those domains;
and perform the separately approved DNS transition. No custom domains, DNS changes,
old-host modifications, original-media writes, final sync or PR merge occurred.
