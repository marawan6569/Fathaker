#!/usr/bin/env python3
"""Explicit offline media pipeline; never connects to Django or its database.

inventory downloads originals by generation; generate creates local candidates;
publish creates immutable objects and verifies every public response before writing
an application manifest. Existing objects are never overwritten or deleted.
"""
import argparse
import base64
from concurrent.futures import ThreadPoolExecutor
import hashlib
from io import BytesIO
import json
from pathlib import Path
import subprocess

from PIL import Image, ImageOps, features
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from google.cloud import storage
from google.api_core.exceptions import PreconditionFailed
from google.oauth2.credentials import Credentials

VERSION = 'v1'
VARIANTS = {'thumb': 128, 'artwork': 768}
CACHE = 'public, max-age=31536000, immutable'


def client():
    token = subprocess.check_output(['gcloud', 'auth', 'print-access-token'], text=True).strip()
    return storage.Client(project='fathaker-quran', credentials=Credentials(token))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def md5(data):
    return base64.b64encode(hashlib.md5(data).digest()).decode()


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


def inspect(data):
    with Image.open(BytesIO(data)) as image:
        image.load()
        alpha = image.convert('RGBA').getchannel('A').getextrema()[0] < 255
        return dict(width=image.width, height=image.height, format=image.format,
                    transparency=alpha, animated=getattr(image, 'is_animated', False))


def inventory(work, bucket):
    blobs = [b for b in bucket.list_blobs(prefix='radio/')
             if not b.name.startswith('radio/optimized/') and not b.name.endswith('/')]
    def download(blob):
        # Pin generation so an in-place edit cannot mix inventory and content.
        data = blob.download_as_bytes(if_generation_match=int(blob.generation))
        assert md5(data) == blob.md5_hash
        digest = sha(data)
        (work / 'originals' / digest).write_bytes(data)
        return dict(key=blob.name, filename=Path(blob.name).name, bytes=len(data),
                    generation=str(blob.generation), md5=blob.md5_hash, sha256=digest,
                    **inspect(data))
    (work / 'originals').mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = sorted(pool.map(download, blobs), key=lambda row: row['key'])
    write_json(work / 'inventory.json', rows)
    print(f"Inventoried {len(rows)} originals, {sum(r['bytes'] for r in rows):,} bytes")


def generate(work, limit):
    assert features.check('webp'), 'Pillow needs WebP support'
    rows = json.loads((work / 'inventory.json').read_text())
    if limit:
        # Broad dimension/size coverage; transparent examples included if present.
        chosen = sorted(rows, key=lambda r: r['bytes'])
        selected = chosen[:1] + chosen[-1:] + sorted(rows, key=lambda r: r['width']/r['height'])[:1]
        selected += [r for r in rows if r['transparency']][:2]
        selected += chosen[::max(1, len(chosen)//limit)]
        rows = list({r['key']: r for r in selected}.values())[:limit]
    manifest = {}
    (work / 'variants').mkdir(exist_ok=True)
    for row in rows:
        entry = dict(source=row, variants={})
        if row['animated']:
            entry['skip'] = 'animated source'
            manifest[row['key']] = entry
            continue
        data = (work / 'originals' / row['sha256']).read_bytes()
        assert sha(data) == row['sha256']
        with Image.open(BytesIO(data)) as original:
            image = ImageOps.exif_transpose(original).convert('RGBA' if row['transparency'] else 'RGB')
            for kind, size in VARIANTS.items():
                resized = image.copy()
                resized.thumbnail((size, size), Image.Resampling.LANCZOS)
                resized.info.clear()
                candidates = []
                for lossless in [False, True]:
                    out = BytesIO()
                    resized.save(out, format='WEBP', quality=84, method=6, lossless=lossless)
                    candidates.append((out.getvalue(), lossless))
                result, lossless = min(candidates, key=lambda item: len(item[0]))
                if len(result) >= row['bytes'] * .95:
                    continue
                key = f'radio/optimized/{VERSION}/{sha(result)}-{kind}.webp'
                (work / 'variants' / Path(key).name).write_bytes(result)
                entry['variants'][kind] = dict(key=key, bytes=len(result), sha256=sha(result),
                    md5=md5(result), lossless=lossless, **inspect(result))
        manifest[row['key']] = entry
    write_json(work / ('pilot.json' if limit else 'candidates.json'), manifest)
    print(f'Generated {sum(len(e["variants"]) for e in manifest.values())} variants from {len(rows)} originals')


def publish(work, bucket, output):
    manifest = json.loads((work / 'candidates.json').read_text())
    def upload_entry(item):
        original, entry = item
        session = requests.Session()
        session.mount('https://', HTTPAdapter(max_retries=Retry(
            total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504]
        )))
        source = entry['source']
        current = bucket.get_blob(original)
        assert str(current.generation) == source['generation'] and current.md5_hash == source['md5'], original
        variants = {}
        for kind, variant in entry['variants'].items():
            data = (work / 'variants' / Path(variant['key']).name).read_bytes()
            assert sha(data) == variant['sha256']
            blob = bucket.blob(variant['key'])
            blob.cache_control = CACHE
            try:
                blob.upload_from_string(data, content_type='image/webp', if_generation_match=0)
            except PreconditionFailed:
                pass  # Idempotent only when the existing immutable object matches exactly.
            blob.reload()
            assert blob.md5_hash == variant['md5'] and blob.size == variant['bytes']
            assert blob.content_type == 'image/webp' and blob.cache_control == CACHE
            response = session.get(blob.public_url, timeout=30, headers={'Accept-Encoding': 'identity'})
            response.raise_for_status()
            assert response.status_code == 200 and response.headers['Content-Type'] == 'image/webp'
            assert sha(response.content) == variant['sha256']
            assert inspect(response.content) == {k: variant[k] for k in inspect(response.content)}
            variants[kind] = variant
        session.close()
        return original, dict(source=source, variants=variants)
    with ThreadPoolExecutor(max_workers=4) as pool:
        verified = dict(pool.map(upload_entry, manifest.items()))
    expected = {v['key'] for e in verified.values() for v in e['variants'].values()}
    actual = {b.name for b in bucket.list_blobs(prefix=f'radio/optimized/{VERSION}/')}
    assert expected <= actual
    # Previous content hashes may coexist after a later regeneration; never delete them.
    write_json(output, {'version': VERSION, 'images': verified})
    print(f'Verified {len(expected)} immutable objects; {len(actual - expected)} retained prior objects')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['inventory', 'generate', 'publish'])
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--bucket', default='fathaker-media')
    parser.add_argument('--pilot', type=int, default=0)
    parser.add_argument('--manifest', type=Path, default=Path('radio/image_manifest.json'))
    args = parser.parse_args()
    args.work.mkdir(parents=True, exist_ok=True)
    if args.action == 'inventory':
        inventory(args.work, client().bucket(args.bucket))
    elif args.action == 'generate':
        generate(args.work, args.pilot)
    else:
        publish(args.work, client().bucket(args.bucket), args.manifest)
