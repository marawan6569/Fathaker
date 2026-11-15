import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils.html import escapejs

from core.models import NavLink
from .images import image_url, load_manifest
from .models import Radio


class RadioImageTests(TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'manifest.json'
        self.manifest_patch = patch('radio.images.MANIFEST_PATH', self.path)
        self.manifest_patch.start()
        self.addCleanup(self.manifest_patch.stop)
        self.addCleanup(load_manifest.cache_clear)
        self.key = 'radio/optimized/v1/' + 'a'*64
        self.path.write_text(json.dumps({'version': 'v1', 'images': {
            'radio/existing.png': {'variants': {
                'thumb': {'key': self.key+'-thumb.webp'},
                'artwork': {'key': self.key+'-artwork.webp'},
            }}
        }}))
        load_manifest.cache_clear()
        NavLink.objects.create(name='radios_list', display_name='Radio', destination='radio:radios_list')
        self.radio = Radio.objects.create(name='إذاعة القرآن', rank=1, image='radio/existing.png')

    def test_manifest_lookup_has_no_queries_or_storage_probes(self):
        with self.assertNumQueries(0), patch.object(self.radio.image.storage, 'exists', side_effect=AssertionError):
            self.assertTrue(image_url(self.radio.image, 'thumb').endswith('-thumb.webp'))
            self.assertTrue(image_url(self.radio.image, 'artwork').endswith('-artwork.webp'))
        self.radio.refresh_from_db()
        self.assertEqual(self.radio.image.name, 'radio/existing.png')

    def test_missing_malformed_and_unknown_manifest_fall_back(self):
        for content in ['{', '{}', '[]', '{"version":"v1","images":[]}',
                        json.dumps({'version':'v1', 'images':{'radio/existing.png':{'variants':{'thumb':{'key':'../unsafe.webp'}}}}})]:
            self.path.write_text(content)
            load_manifest.cache_clear()
            self.assertEqual(image_url(self.radio.image, 'thumb'), self.radio.image.url)
        self.path.unlink()
        load_manifest.cache_clear()
        self.assertEqual(image_url(self.radio.image, 'thumb'), self.radio.image.url)

    def test_new_upload_and_no_image_fallback(self):
        self.radio.image.name = 'radio/new-upload.png'
        self.assertEqual(image_url(self.radio.image, 'thumb'), self.radio.image.url)
        self.radio.image = ''
        self.assertIn('radio_img_not_available.png', image_url(self.radio.image, 'artwork'))

    def test_list_and_unicode_detail_keep_original_social_image(self):
        response = self.client.get(reverse('radio:radios_list'))
        self.assertContains(response, escapejs(self.key+'-thumb.webp'))
        self.assertContains(response, escapejs(self.key+'-artwork.webp'))
        response = self.client.get(reverse('radio:radio_detail', kwargs={'slug':self.radio.slug}))
        self.assertContains(response, self.key+'-artwork.webp')
        self.assertContains(response, '<meta property="og:image" content="http://testserver/media/radio/existing.png">')
        self.radio.refresh_from_db()
        self.assertEqual(self.radio.image.name, 'radio/existing.png')


class ConversionTests(TestCase):
    def test_transparency_aspect_ratio_no_upscale_metadata_and_idempotency(self):
        from deployment.optimize_radio_images import generate, inspect, sha
        from PIL import Image
        from io import BytesIO
        with TemporaryDirectory() as directory:
            work = Path(directory)
            (work/'originals').mkdir()
            image = Image.new('RGBA', (80, 40), (255, 0, 0, 120))
            output = BytesIO()
            image.save(output, format='PNG')
            data = output.getvalue()
            digest = sha(data)
            (work/'originals'/digest).write_bytes(data)
            (work/'inventory.json').write_text(json.dumps([dict(key='radio/test.png', bytes=len(data),sha256=digest,**inspect(data))]))
            generate(work, 0)
            first = (work/'candidates.json').read_bytes()
            generate(work, 0)
            self.assertEqual(first, (work/'candidates.json').read_bytes())
            variants = json.loads(first)['radio/test.png']['variants']
            self.assertEqual(len(variants), 2)
            for variant in variants.values():
                self.assertEqual((variant['width'],variant['height']), (80,40))
                self.assertTrue(variant['transparency'])
                self.assertEqual(variant['format'], 'WEBP')
                self.assertLess(variant['bytes'],len(data))
