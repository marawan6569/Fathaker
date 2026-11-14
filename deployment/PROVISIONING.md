# Fathaker provisioning record and remaining deployment

Project discovered from the authenticated Google Cloud CLI, not inferred from its
name: **fathaker-quran**, number **251791733172**, display name **Fathaker**.
Billing is enabled. All commands below explicitly select this existing project.
Do not create a second project, service-account keys, or Cloud SQL.

## Provisioned resources

| Resource | Configuration |
| --- | --- |
| Media bucket | `gs://fathaker-media`, Standard, `us-east1`, uniform bucket access, Google-managed encryption, public object reads |
| Runtime identity | `fathaker-runtime@fathaker-quran.iam.gserviceaccount.com` |
| Docker registry | `us-east1-docker.pkg.dev/fathaker-quran/fathaker` (empty; scanning disabled) |
| Django secret | `fathaker-django-secret-key`, version `1`, generated securely without logging its value |
| Database secret | `fathaker-database-url`, no version yet; never populated with a dummy database |
| Secret replication | One user-managed replica in `us-east1`, Google-managed encryption |
| Budget | Project-only USD 5/month, 50%/90%/100% actual and 100% forecast alerts; excludes credits |

The existing USD 35 account budget was retained. Budget alerts go to billing IAM
recipients (the authenticated project owner is also a billing administrator).
Budgets are notifications, not spending caps. Excluding credits means the new alert
can trigger while free-tier/trial credits still cover the invoice.

Explicitly enabled `run.googleapis.com`, `artifactregistry.googleapis.com`,
`secretmanager.googleapis.com`, `iam.googleapis.com`, and
`billingbudgets.googleapis.com`. Storage, logging, monitoring, and Service Usage
were already enabled. Google also enables API dependencies; unrelated pre-existing
APIs were not disabled or used to provision additional services.

Runtime permissions are only `roles/storage.objectUser` on the media bucket and
`roles/secretmanager.secretAccessor` on each of the two named secrets. No
project-level role or user-managed key was added to the runtime service account.
Public access is bucket-scoped `allUsers` / `roles/storage.objectViewer`, enabled
only after inspecting the source assets and verifying the cloud inventory.
Cloud Run's managed service agent handles same-project image pulls; the runtime
identity does not need an Artifact Registry writer or project Editor role.

No Cloud Run service/revision, Firebase Hosting release, DNS change, or application
image push has been performed. An application service needs the real imported Neon
database, so CPU/memory/scaling limits will take effect at deployment, not before.

## Media migration

The user confirmed the repository's local `media/` is the authoritative production
media source. File-type and visual inspection found only radio PNG artwork/portraits,
with no non-image files, hidden paths, symlinks, or PNG metadata.

A private verified backup is outside the repository:
`~/Documents/Fathaker-migration-backups/media-20261114T025215Z/`.
Its `manifest.json` records all relative names, byte counts, SHA-256, MD5, and CRC32C;
`media/` contains the separate backup files. The backup directory is private, and
only its `media/` contents are eligible for the public bucket, never the manifest,
logs, database snapshots, or credentials. Original source files are retained.

Source inventory: **154 PNGs, 310,443,753 bytes**. Existing object keys start with
`radio/`, not `media/radio/`. There are no Unicode filenames in the source inventory.
Verification completed successfully:

- Exact cloud/source key-set equality and total byte count: **154 / 310,443,753**.
- Every cloud object's MD5, CRC32C, size, and `image/png` type match the backup.
- Unauthenticated HTTPS HEAD succeeded for **all 154 image URLs**.
- Three representative public downloads matched the source SHA-256 hashes.
- A temporary copy of an existing public image with an Arabic filename passed a
  percent-encoded URL/download/SHA-256 round trip. Only that unique verification
  copy was removed, with a generation precondition; all original keys remain.
- Final bucket key set is exactly the original 154 keys. Source and backup were
  rehashed after migration and remain unchanged.

Private evidence is stored next to the backup in `gcs-inventory-verification.json`,
`public-verification.json`, and `upload.log`. No production database was read or
modified. Database-to-image-reference verification remains part of the Neon import.
Any content added after this snapshot needs a final verified sync before cutover.

## Remaining steps (commands are preparation, not already executed)

### 1. Neon and fixtures

Create a Neon PostgreSQL project/database in **AWS us-east-1**, if available. Keep
its default scale-to-zero behavior. Obtain the **direct** URL for migration and
**pooled** URL for runtime. Preserve Neon's TLS parameters (`sslmode=require`, plus
`channel_binding=require` if supplied); URL-encode special password characters.

Follow [MIGRATION.md](MIGRATION.md#sqlite-to-postgresql) on an authorized consistent
SQLite working snapshot. Use the direct Neon URL with `DEBLOYED=0 DEBUG=0` for CLI
migration/import; GCS credentials are unnecessary because fixtures contain file
names. Run all migrations, load natural-key permissions before the main fixture,
and verify all content/relationships/sequences. Never point tests at production.

After the actual import is verified, add the pooled URL as a new version of
`fathaker-database-url`. To avoid shell history, files, and printed secrets, use a
local terminal prompt with the authenticated gcloud CLI:

```python
import getpass
import subprocess

url = getpass.getpass('Verified Neon pooled DATABASE_URL: ')
subprocess.run([
    'gcloud', 'secrets', 'versions', 'add', 'fathaker-database-url',
    '--data-file=-', '--project=fathaker-quran', '--quiet',
], input=url.encode(), check=True)
```

Use the returned numeric version below. Do not paste credentials into Git, a PR,
chat, environment examples, or command-line arguments. The first database secret
version will normally be `1`; verify it rather than assuming.

### 2. Build and deploy the approved application

Keep PR #24 unmerged until it is approved. At the deployment phase, build the
approved commit with Docker (no Cloud Build service is necessary):

```sh
gcloud auth configure-docker us-east1-docker.pkg.dev --project=fathaker-quran
FATHAKER_IMAGE="us-east1-docker.pkg.dev/fathaker-quran/fathaker/web:$(git rev-parse --short HEAD)"
docker build --platform=linux/amd64 -t "$FATHAKER_IMAGE" .
docker push "$FATHAKER_IMAGE"
```

Ensure the Google Cloud SDK `bin` directory is on PATH for both `gcloud` and the
Docker credential helper. Do not build from a directory containing unignored secrets.
The reviewed `.dockerignore` excludes media, SQLite, backups, and `.env` files.

Set `FATHAKER_DATABASE_SECRET_VERSION` to the verified numeric version. The initial
host list intentionally contains only known domains; add the actual generated Run
URL immediately after creation, before web verification:

```sh
: "${FATHAKER_IMAGE:?Set the image built from the approved commit}"
: "${FATHAKER_DATABASE_SECRET_VERSION:?Set the imported Neon secret version}"
gcloud run deploy fathaker \
  --project=fathaker-quran --region=us-east1 --platform=managed \
  --image="$FATHAKER_IMAGE" \
  --service-account=fathaker-runtime@fathaker-quran.iam.gserviceaccount.com \
  --cpu=1 --memory=512Mi --min=0 --max=2 --concurrency=4 \
  --cpu-throttling --no-cpu-boost --port=8080 --timeout=60 \
  --allow-unauthenticated --ingress=all \
  --set-env-vars='DEBLOYED=1,DEBUG=0,GS_BUCKET_NAME=fathaker-media,ALLOWEDHOSTS=fathaker.com;www.fathaker.com,TRUSTEDORIGINS=https://fathaker.com;https://www.fathaker.com' \
  --set-secrets="SECRETKEY=fathaker-django-secret-key:1,DATABASE_URL=fathaker-database-url:${FATHAKER_DATABASE_SECRET_VERSION}"

FATHAKER_RUN_URL="$(gcloud run services describe fathaker --region=us-east1 \
  --project=fathaker-quran --format='value(status.url)')"
FATHAKER_RUN_HOST="${FATHAKER_RUN_URL#https://}"
gcloud run services update fathaker --region=us-east1 --project=fathaker-quran \
  --update-env-vars="ALLOWEDHOSTS=fathaker.com;www.fathaker.com;${FATHAKER_RUN_HOST},TRUSTEDORIGINS=https://fathaker.com;https://www.fathaker.com;${FATHAKER_RUN_URL}"
```

`--cpu-throttling` selects request-based billing. Service-level `--max=2` constrains
the service across revisions; it is still not an absolute billing cap. There is no
VPC connector or load balancer. Cloud Run supplies `PORT`; the attached identity
supplies GCS credentials. No SQLite or media volume mounts belong on Cloud Run.

Run the admin/API/radio/search/Unicode/static/media smoke tests through the actual
Run URL, including a new image upload and restart persistence. Confirm the resource
limits, attached identity, secret versions, and billing mode on the created service.

### 3. Firebase Hosting

Add Firebase to the **existing** `fathaker-quran` project, selecting the billing plan
required for Hosting-to-Cloud-Run rewrites. This is Firebase Hosting, not App Hosting.
At this point enable only the Firebase/Hosting APIs required by that operation.
Do not create a second project or a service-account key to authenticate Firebase.

Use `deployment/firebase/firebase.json`: all paths rewrite to service `fathaker`
in `us-east1`; static files stay with WhiteNoise. Use the authenticated Firebase CLI
(or the Hosting REST API authorized with the existing gcloud session) to publish
this configuration only after Run verification. For an authenticated Firebase CLI:

```sh
cd deployment/firebase
firebase deploy --only hosting --project fathaker-quran
```

Discover the actual Hosting site/preview domains. Append them to the existing
`ALLOWEDHOSTS` and their HTTPS origins to `TRUSTEDORIGINS`; do not remove the Run or
custom-domain entries. Verify admin login/logout, session messages, CSRF-protected
POSTs and uploads through Hosting. `__session` is the only forwarded cookie;
production settings already use session-backed CSRF/messages and dynamic no-store.

### 4. Final cutover

Freeze old-host content edits/uploads for the final database export and media sync.
Preserve all new content if a rehearsal was done earlier; a few counter writes may
be lost. Repeat count/key/size/checksum verification before DNS changes.

Add `fathaker.com` and `www.fathaker.com` to Firebase Hosting. Use exactly the
verification and DNS records Firebase returns, keeping Cloudflare **DNS-only** for
this migration. Wait for the managed certificates; verify redirects, host/CSRF
handling, public images, static files, and application behavior. Keep the old host
and private backups until accepted. Cloudflare CDN tuning is a later task.

## Cost expectations

Current resources have no fixed compute cost: Run is not deployed, the registry is
empty, and there is one active secret version. The media occupies about 0.289 GiB.
Expected incremental monthly cost is approximately **USD 0 if the billing account's
free allowances remain available**, excluding future traffic. After deployment,
a small low-traffic site may remain near zero, but traffic, Neon/Firebase quotas,
image retention, log volume, and shared free-tier consumption determine the bill.

Reference allowances: GCS 5 GB-months/5,000 Class A/50,000 Class B operations and
eligible North America egress; Artifact Registry 0.5 GB storage; Secret Manager six
active versions/10,000 accesses; request-based Run 180,000 vCPU-seconds,
360,000 GiB-seconds and two million requests per month. Allowances are shared across
the billing account. Storage soft-delete retains deleted objects for seven days;
versioning, Autoclass, paid image scanning, and replication were not added.

Prices checked during provisioning:
[GCS](https://cloud.google.com/storage/pricing),
[Artifact Registry](https://cloud.google.com/artifact-registry/pricing),
[Secret Manager](https://cloud.google.com/secret-manager/pricing),
[Cloud Run](https://cloud.google.com/run/pricing).
