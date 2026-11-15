#!/usr/bin/env python3
"""Deploy this empty-public-directory Hosting rewrite using gcloud user credentials.

No CLI login token, key file, local static upload, app build or domain attachment.
Requires the existing Firebase project/site and the Hosting API to be enabled.
"""
import json
from pathlib import Path
import subprocess
import requests

PROJECT = 'fathaker-quran'
root = Path(__file__).resolve().parent
config = json.loads((root / 'firebase.json').read_text())['hosting']
public = root / config['public']
assert public.is_dir() and not [p for p in public.rglob('*') if p.is_file() and p.name != '.gitkeep']
assert config['site'] == PROJECT
assert config['rewrites'] == [{'source': '**', 'run': {'serviceId': 'fathaker', 'region': 'us-east1'}}]
session = requests.Session()
session.headers.update({
    'Authorization': 'Bearer ' + subprocess.check_output(
        ['gcloud', 'auth', 'print-access-token'], text=True).strip(),
    'x-goog-user-project': PROJECT,
})
base = 'https://firebasehosting.googleapis.com/v1beta1/'


def api(method, path, **kwargs):
    response = session.request(method, base + path, timeout=60, **kwargs)
    response.raise_for_status()
    return response.json()


version = api('POST', f'sites/{PROJECT}/versions', json={'config': {'rewrites': [
    {'glob': '**', 'run': config['rewrites'][0]['run']}
]}})['name']
api('POST', version + ':populateFiles', json={'files': {}})
api('PATCH', version, params={'updateMask': 'status'}, json={'status': 'FINALIZED'})
release = api('POST', f'sites/{PROJECT}/releases', params={'versionName': version},
              json={'message': 'Catch-all Django Cloud Run rewrite; no revision pinning'})
print(json.dumps({'release': release['name'], 'version': version,
                  'url': f'https://{PROJECT}.web.app'}, indent=2))
