"""Local verified media manifest. No storage or database requests for lookup."""
from functools import lru_cache
import json
from pathlib import Path
import re

from django.templatetags.static import static

MANIFEST_PATH = Path(__file__).with_name('image_manifest.json')
KEY = re.compile(r'^radio/optimized/v1/[a-f0-9]{64}-(thumb|artwork)\.webp$')


@lru_cache(maxsize=1)
def load_manifest():
    try:
        manifest = json.loads(MANIFEST_PATH.read_text())
        return manifest['images'] if manifest['version'] == 'v1' and isinstance(manifest['images'], dict) else {}
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return {}


def image_url(image, variant):
    if not image or not image.name:
        return static('radio/img/radio_img_not_available.png')
    try:
        item = load_manifest().get(image.name, {}).get('variants', {}).get(variant, {})
        key = item.get('key', '')
        if KEY.fullmatch(key) and key.endswith(f'-{variant}.webp'):
            return image.storage.url(key)
    except (TypeError, AttributeError):
        pass
    return image.url
