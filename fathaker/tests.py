import os
import runpy
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from core.models import NavLink
from radio.models import Radio


class SettingsTests(SimpleTestCase):
    production = {
        'DEBLOYED': '1',
        'SECRETKEY': 'test-only-key-with-at-least-fifty-characters-for-system-checks',
        'ALLOWEDHOSTS': 'fathaker.com',
        'TRUSTEDORIGINS': 'https://fathaker.com',
        'DATABASE_URL': 'postgresql://test:test@localhost/test?sslmode=require',
        'GS_BUCKET_NAME': 'test-media',
    }

    def load_settings(self, env):
        with patch.dict(os.environ, env, clear=True), patch('dotenv.load_dotenv'):
            return runpy.run_path(str(Path(__file__).with_name('settings.py')))

    def test_local_sqlite_snapshot_is_explicitly_selectable(self):
        settings = self.load_settings({'SQLITE_PATH': '/tmp/disposable-snapshot.sqlite3'})
        self.assertEqual(settings['DATABASES']['default']['NAME'], '/tmp/disposable-snapshot.sqlite3')
        self.assertNotEqual(settings['STATIC_ROOT'], settings['STATICFILES_DIRS'][0])

    def test_production_requires_database_and_bucket(self):
        from django.core.exceptions import ImproperlyConfigured
        for name in ('DATABASE_URL', 'GS_BUCKET_NAME', 'SECRETKEY', 'ALLOWEDHOSTS', 'TRUSTEDORIGINS'):
            with self.subTest(name=name):
                env = self.production.copy()
                del env[name]
                with self.assertRaisesMessage(ImproperlyConfigured, name):
                    self.load_settings(env)

    def test_cloud_run_cannot_silently_use_local_mode(self):
        from django.core.exceptions import ImproperlyConfigured
        with self.assertRaisesMessage(ImproperlyConfigured, 'SECRETKEY'):
            self.load_settings({'K_SERVICE': 'fathaker', 'DEBLOYED': '0'})

    def test_production_rejects_debug_and_sqlite_url(self):
        from django.core.exceptions import ImproperlyConfigured
        for override in ({'DEBUG': '1'}, {'DATABASE_URL': 'sqlite:///unsafe.sqlite3'}):
            with self.subTest(override=override), self.assertRaises(ImproperlyConfigured):
                self.load_settings({**self.production, **override})

    def test_production_storage_and_database_options(self):
        settings = self.load_settings(self.production)
        database = settings['DATABASES']['default']
        self.assertEqual(database['ENGINE'], 'django.db.backends.postgresql')
        self.assertEqual(database['OPTIONS']['sslmode'], 'require')
        self.assertEqual(database['CONN_MAX_AGE'], 0)
        self.assertTrue(database['DISABLE_SERVER_SIDE_CURSORS'])
        strict = self.load_settings({**self.production, 'DATABASE_URL':
                                     self.production['DATABASE_URL'].replace('sslmode=require', 'sslmode=verify-full')})
        self.assertEqual(strict['DATABASES']['default']['OPTIONS']['sslmode'], 'verify-full')
        storage = settings['STORAGES']['default']
        self.assertEqual(storage['BACKEND'], 'storages.backends.gcloud.GoogleCloudStorage')
        self.assertFalse(storage['OPTIONS']['file_overwrite'])
        self.assertEqual(storage['OPTIONS']['location'], '')
        self.assertFalse(storage['OPTIONS']['querystring_auth'])


@override_settings(
    SESSION_COOKIE_NAME='__session',
    SESSION_COOKIE_SECURE=True,
    CSRF_USE_SESSIONS=True,
    MESSAGE_STORAGE='django.contrib.messages.storage.session.SessionStorage',
    SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO', 'https'),
    SECURE_SSL_REDIRECT=True,
    MIDDLEWARE=[
        'django.middleware.security.SecurityMiddleware',
        'whitenoise.middleware.WhiteNoiseMiddleware',
        'fathaker.middleware.NoStoreMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
    ],
)
class FirebaseSessionTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True, HTTP_HOST='testserver', HTTP_X_FORWARDED_PROTO='https',
                             HTTP_ORIGIN='https://testserver')
        User.objects.create_superuser('migration-admin', 'admin@example.test', 'test-only-password')
        NavLink.objects.create(name='radios_list', display_name='Radio', destination='radio:radios_list')
        self.radio = Radio.objects.create(name='إذاعة القرآن', rank=1)

    def keep_forwarded_cookie_only(self):
        for name in list(self.client.cookies):
            if name != '__session':
                del self.client.cookies[name]

    def test_admin_login_and_authenticated_like_through_firebase_cookie_filter(self):
        login_url = reverse('admin:login')
        response = self.client.get(login_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Cache-Control'], 'private, no-store')
        token = str(response.context['csrf_token'])
        self.assertTrue(self.client.cookies['__session']['secure'])
        self.assertNotIn('csrftoken', self.client.cookies)
        self.keep_forwarded_cookie_only()
        response = self.client.post(login_url, {
            'username': 'migration-admin', 'password': 'test-only-password',
            'csrfmiddlewaretoken': token, 'next': reverse('admin:index'),
        })
        self.assertEqual(response.status_code, 302, response.content.decode())
        self.keep_forwarded_cookie_only()
        self.assertEqual(self.client.get(reverse('admin:index')).status_code, 200)
        page = self.client.get(reverse('radio:radio_detail', kwargs={'slug': self.radio.slug}))
        token = str(page.context['csrf_token'])
        url = reverse('radio:radio_like', kwargs={'slug': self.radio.slug})
        self.assertEqual(self.client.post(url).status_code, 403)
        self.assertEqual(self.client.post(url, HTTP_X_CSRFTOKEN=token).status_code, 200)
        self.radio.refresh_from_db()
        self.assertEqual(self.radio.likes_count, 1)


class GCSUploadTests(TestCase):
    def test_imagefield_upload_uses_gcs_and_does_not_overwrite_existing_key(self):
        from django.core.files.base import ContentFile
        from unittest.mock import Mock
        from storages.backends.gcloud import GoogleCloudStorage

        settings = SettingsTests().load_settings(SettingsTests.production)
        with override_settings(STORAGES=settings['STORAGES']), \
                patch('storages.backends.gcloud.Client') as client, \
                patch('storages.backends.gcloud.Blob') as blob:
            # The original key exists; the generated alternative and its new blob do not.
            bucket = client.return_value.bucket.return_value
            bucket.get_blob.side_effect = [Mock(), None, None]
            radio = Radio.objects.create(name='Upload test', rank=1)
            self.assertIsInstance(radio.image.storage, GoogleCloudStorage)
            radio.image.save('photo.png', ContentFile(b'synthetic-upload', name='photo.png'))
            self.assertRegex(radio.image.name, r'^radio/photo_[A-Za-z0-9]+\.png$')
            radio.refresh_from_db()
            self.assertTrue(radio.image.name.startswith('radio/'))
            client.return_value.bucket.assert_called_with('test-media')
            blob.assert_called_once_with(radio.image.name, bucket, chunk_size=None)
            blob.return_value.upload_from_file.assert_called_once()
            self.assertIsNone(blob.return_value.upload_from_file.call_args.kwargs['predefined_acl'])
