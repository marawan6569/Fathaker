# Fathaker hosting migration

Code preparation only. Provisioning, production exports, DNS changes, and deployment
are separate steps. Never run the old `backup.py` or `import_mutashabihat` as a restore.

For the provisioned project, resource names, media verification, and exact remaining
commands, see [PROVISIONING.md](PROVISIONING.md).

## Runtime

Python 3.12; Django 5.2.19 LTS; Cloud Run in `us-east1`; Neon in AWS
`us-east-1` if available. The Docker image serves static assets with WhiteNoise;
media goes to GCS using the attached Cloud Run service account. No Nginx, mounted
media filesystem, VPC connector, or database migration on container startup.

Set these on Cloud Run (values below are placeholders, not credentials):

| Variable | Value |
| --- | --- |
| `DEBLOYED` | `1` (legacy spelling retained) |
| `DEBUG` | `0` |
| `SECRETKEY` | Secret Manager reference to a strong Django secret |
| `DATABASE_URL` | Secret Manager reference to the Neon **pooled** PostgreSQL connection URL, including `sslmode=require` and Neon-provided TLS options |
| `GS_BUCKET_NAME` | The public media bucket name, without `gs://` |
| `ALLOWEDHOSTS` | `fathaker.com;www.fathaker.com;ACTUAL_SERVICE_HOST.run.app;PROJECT.web.app;PROJECT.firebaseapp.com` |
| `TRUSTEDORIGINS` | The same selected hosts as full `https://` origins, separated by `;` |

Use exact hosts from the provisioned services, not the illustrative hostnames.
`PORT` comes from Cloud Run; do not set `GOOGLE_APPLICATION_CREDENTIALS`. The runtime
service account needs bucket-level `roles/storage.objectUser` and
`roles/secretmanager.secretAccessor` on the two referenced secrets. No project-wide
storage role or service-account key file is needed.

Start with request-based billing, minimum instances 0, maximum instances 2,
1 vCPU, 512 MiB, concurrency 4. Gunicorn runs one worker/four threads. Verify
cold-start latency and memory before increasing capacity. Use an Artifact Registry
repository for the image; a local Docker build/push avoids adding a build service.
Set budget alerts; they are not spending caps.

Production fails without its required database, bucket, hosts, origins, or secret;
`K_SERVICE` also forces production mode. PostgreSQL connections close after each
request and server-side cursors are disabled for Neon's transaction pooler.

## Local development and image checks

Copy `deployment/.env.example` to `.env` for optional local settings. Without
`DATABASE_URL`, local mode uses SQLite; `SQLITE_PATH` selects a disposable database
or snapshot. Production never falls back to SQLite. `DATABASE_URL` only accepts
PostgreSQL URLs. `load_dotenv` never overrides supplied environment variables.

```sh
python -m pip install -r requirements.txt
DEBLOYED=0 DATABASE_URL='' SQLITE_PATH=:memory: python manage.py test --noinput
DEBLOYED=0 DATABASE_URL='' SQLITE_PATH=:memory: python manage.py check
DEBLOYED=0 DATABASE_URL='' SQLITE_PATH=:memory: python manage.py makemigrations --check --dry-run
DEBLOYED=0 DEBUG=0 DATABASE_URL='' SQLITE_PATH=:memory: python manage.py collectstatic --noinput
docker build -t fathaker:local .
```

The image collects static files without credentials or a database connection.
`static/` is the source and `staticfiles/` the build output. Non-manifest compressed
storage deliberately tolerates the existing absent Bootstrap source map.

Compose is for local development only and retains the existing SQLite/media mounts.
It serves port 8000 on the host, 8080 in the container. It does not run migrations
implicitly. For an explicit management command, the entrypoint forwards arguments:
`docker run --rm ... fathaker:local python manage.py check`.
Do not use the production database for local checks/tests.

## GCS: first provisioning and media copy

1. Confirm all files intended for this bucket are public website media. Keep database
   snapshots and exports in private backup storage, never in this public bucket.
2. Create one **Standard**, regional `us-east1` bucket with uniform bucket-level
   access. Public access prevention must not be enforced on this public-media bucket
   or by an ancestor policy. Grant `allUsers` `roles/storage.objectViewer` on it and
   grant the runtime identity `roles/storage.objectUser` on this bucket only.
3. Make a verified off-server media backup. Copy the **contents** of the source
   media directory, retaining all keys, including unreferenced files:

   ```sh
   gcloud storage rsync --recursive /verified-snapshot/media/ gs://YOUR_BUCKET/
   gcloud storage rsync --recursive --checksums-only --dry-run /verified-snapshot/media/ gs://YOUR_BUCKET/
   ```

   Do not use a destination `media/` prefix or deletion flags. Compare the complete
   inventory, byte sizes, and checksums. Test unauthenticated reads of representative
   image URLs, including Unicode names, before switching storage.
4. Configure `GS_BUCKET_NAME` on the new service. Existing `Radio.image` names such
   as `radio/example.jpg` remain unchanged. `file_overwrite=False` preserves local
   collision behavior for future uploads; a reused filename gets a new key.
5. For cutover, freeze content edits/uploads on the old service and repeat the sync.
   Verify every nonempty image field maps to an object. Test one new admin upload
   after the new service is approved; restarting it must not lose that upload.

No CORS configuration is needed for ordinary image display. `Audio.url` and
`Radio.stream_url` are URLFields, not stored files: inspect snapshot values for
old-host URLs, local media URLs, and HTTP-only sources separately. The storage
backend cannot rewrite these. If old `/media/...` URLs have external consumers,
add a targeted redirect to the corresponding GCS object before retiring the old host.

## SQLite to PostgreSQL

### Prepare and rehearse

- Record the production code revision, dependency versions, and applied migration
  history. Confirm parity with the export code. Files under `radio/migrations/old/`
  are archived, not part of the active graph. Never fake migrations to hide a mismatch.
- Obtain a consistent SQLite backup using SQLite's online backup facility or a
  stopped writer. Copying only a live SQLite file can omit WAL data. Preserve an
  untouched original off-server; work on a separate copy.
- If the source schema is older, apply the necessary migrations to a disposable
  working copy first and compare content. The taggit upgrade has its own migrations;
  include those when bringing the working copy and empty target to matching state.
- Inspect string lengths/types, invalid null characters, uniqueness, foreign keys,
  image names, custom permissions, and any absolute media URLs. PostgreSQL enforces
  constraints more strictly than SQLite. Verify all radios have nonempty unique
  slugs and ranks; `loaddata` bypasses `Radio.save()`.

### Export the working snapshot

Run in a shell with **no** `K_SERVICE`, `DEBLOYED=0`, `DEBUG=0`,
`DATABASE_URL=''`, and `SQLITE_PATH` set to the absolute working snapshot path.
Use a private directory outside the repository/image context (`umask 077`).

```sh
python manage.py showmigrations
python manage.py dumpdata --all --natural-foreign \
  --exclude contenttypes --exclude auth.permission --exclude sessions.session \
  --output /private/export/migration.json
python manage.py dumpdata auth.permission --all --natural-foreign --natural-primary \
  --output /private/export/permissions.json
```

The main fixture retains numeric primary keys; **do not** add `--natural-primary`
to it. It includes users/password hashes, groups, admin logs, navigation, radios,
tags/tagged items, surahs, verses, audio M2M links, phrases, and phrase occurrences.
`verses.models` explicitly registers both mutashabihat models for management commands.
Check these model labels in the export: `verses.phrase`, `verses.phraseoccurrence`.
Zero rows are acceptable only if the verified source has zero rows.

Content types and default permissions are regenerated by migrations. The separate
permission fixture uses natural primary keys to merge default permissions and
preserve custom permissions before user/group assignments load. If custom permissions
or admin logs refer to obsolete content types, preserve those content types in a
separate natural-key fixture and load it first; do not silently discard records.
Sessions are intentionally omitted (users sign in again). Fixtures contain sensitive
account data and must not enter Git, images, logs, or the public media bucket.

### Import into a new empty Neon database

Use the **direct** Neon URL, including TLS options, from the operator environment.
For this CLI operation `DEBLOYED=0 DEBUG=0` permits local storage without GCS
credentials; the explicitly supplied `DATABASE_URL` selects PostgreSQL. Loading
image fields imports names only and does not upload files. Inspect the target
hostname/database privately before running commands; never print credentials.

```sh
python manage.py migrate --noinput
python manage.py loaddata /private/export/permissions.json /private/export/migration.json
python manage.py check
python manage.py makemigrations --check --dry-run
```

Run all migrations before importing; do not create a replacement superuser or seed
content beforehand. Never use `--ignorenonexistent`. Failed rehearsals should be
retried in a fresh disposable database, not merged into an active database.
`loaddata` restores relationships and resets PostgreSQL sequences for loaded models.
Check sequences for automatic M2M tables as well as ordinary model tables before
acceptance; don't blindly run sequence-reset SQL on production.

### Acceptance

Compare source/target per-model counts and PK-ordered content (canonical JSON or
hashes), excluding only sessions/regenerated identifiers and explicitly accepted
counter differences. Validate:

- Quran text, verse identifiers, surah relationships, audio links, phrases and
  occurrences; source completeness, not just a presumed verse count.
- Radio slugs/ranks/tags, taggit generic content-type/object-ID references, and images.
- Users/password hashes, group memberships, custom permissions, admin logs, NavLinks.
- Arabic searches with/without tashkeel, Unicode radio routes, mushaf and phrase APIs.
- New records receive IDs greater than existing maxima; disposable inserts exercise
  sequences. A synthetic SQLite-to-PostgreSQL rehearsal is available as
  `deployment/rehearse_migration.py` (see its usage).
- Every media key exists, checksums match, streams/audio play, and admin login works.

For final export, freeze content edits/uploads through verification and DNS cutover;
a few like/view writes may be lost. Keep the old service and untouched backups.
Once new content writes resume, rollback must also preserve those new records/files.

## Firebase Hosting and DNS (after Cloud Run verification)

`deployment/firebase/firebase.json` rewrites all paths to Cloud Run service
`fathaker` in `us-east1`; adjust the service ID if necessary. The empty Hosting public
directory deliberately leaves static serving to WhiteNoise. Select the GCP/Firebase
project explicitly with the Firebase CLI. This is Firebase Hosting, not App Hosting.
Enable the billing plan required for the Cloud Run integration.

Allow unauthenticated Cloud Run invocation for the public website. Add the Firebase
preview hosts to `ALLOWEDHOSTS` and `TRUSTEDORIGINS`. Test through Hosting before
attaching `fathaker.com` and `www.fathaker.com`. Follow Firebase's domain-verification
and DNS records in Cloudflare with **DNS-only** records initially; wait for its
certificate and verify HTTPS before cutover. Do not point a bare CNAME at `run.app`.

Firebase forwards only `__session`: production settings use that session cookie,
session-backed CSRF and messages. Templates already send CSRF tokens to AJAX likes.
Dynamic responses are `private, no-store`; WhiteNoise handles static cache headers.
Test admin login/logout, authenticated and anonymous likes, admin forms/uploads,
and messages with the proxy's cookie filtering. Hosting has a 60-second request
limit; browser radio streams go directly to their URL and are not proxied by Django.

Run production `check --deploy` with runtime variables. HSTS starts at one hour;
include-subdomains and preload are intentionally off pending domain-wide review.
No Cloudflare CDN tuning is required for this migration.

## Code-phase validation

Validated on Python 3.12 with disposable SQLite and PostgreSQL 17: all 30 tests
pass on each database. The synthetic cross-database rehearsal preserved all 14
records across 12 exported models exactly, including custom permission assignments,
taggit references, mutashabihat, audio M2M links, and Unicode media names. All
populated integer sequences (including automatic M2M tables) passed checks.

`pip check`, Django system checks, migration drift checks, static collection,
Compose validation, and Docker build passed. The image served static files with
`DEBUG=0` on a custom `PORT=9090`, honored forwarded HTTPS, redirected HTTP,
and returned dynamic `private, no-store` headers. Image inspection found no `.env`,
SQLite database, media directory, or Git history. GCS upload behavior was mocked;
no cloud or production data was used.

`check --deploy` has no errors but reports five warnings: three drf-spectacular
warnings for missing API response serializer annotations (MushafPageAPI,
MutashabihatByAyah, MutashabihatSearch), and the two intentionally disabled HSTS
include-subdomains/preload options. API annotation cleanup is outside this migration.
Live Neon TLS/pooling, GCS IAM/public access, Firebase certificates and proxy behavior,
production content completeness, and upload persistence still need provisioning-phase
verification. Local tests simulate Firebase cookie filtering; they do not replace
that live smoke test.

References: [Cloud Run contract](https://cloud.google.com/run/docs/container-contract),
[Firebase cookies](https://firebase.google.com/docs/hosting/manage-cache),
[GCS storage options](https://django-storages.readthedocs.io/en/latest/backends/gcloud.html),
[Neon Django](https://neon.com/docs/guides/django).
