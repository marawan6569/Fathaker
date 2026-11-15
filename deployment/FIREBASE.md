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

Live CDN evidence and final deployed digest will be appended after validation.
