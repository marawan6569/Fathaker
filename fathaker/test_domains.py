from django.contrib.auth.models import User
from django.http import HttpResponse
from django.test import Client, RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from core.models import NavLink
from radio.models import Radio
from .middleware import NoStoreMiddleware

HOSTS = ('fathaker.com', 'www.fathaker.com')
ORIGIN = 'fathaker-kc557mz5kq-ue.a.run.app'


@override_settings(ALLOWED_HOSTS=[ORIGIN, *HOSTS])
class ForwardedDomainTests(SimpleTestCase):
    def test_both_headers_restore_absolute_urls_for_each_production_domain(self):
        for header in ['HTTP_X_FH_REQUESTED_HOST', 'HTTP_X_FORWARDED_HOST']:
            for host in HOSTS:
                with self.subTest(header=header, host=host):
                    request = RequestFactory().get('/radio/?q=1', HTTP_HOST=ORIGIN,
                        HTTP_X_FORWARDED_PROTO='https', **{header: host})
                    with override_settings(SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO', 'https')):
                        response = NoStoreMiddleware(lambda r: HttpResponse(r.build_absolute_uri()))(request)
                    self.assertEqual(response.content.decode(), f'https://{host}/radio/?q=1')

    def test_untrusted_forwarded_values_are_ignored(self):
        for host in ['attacker.test', 'fathaker.com.attacker.test', 'www.fathaker.com:443',
                     'fathaker.com,attacker.test', 'https://fathaker.com']:
            request = RequestFactory().get('/', HTTP_HOST=ORIGIN, HTTP_X_FORWARDED_HOST=host)
            response = NoStoreMiddleware(lambda r: HttpResponse(r.get_host()))(request)
            self.assertEqual(response.content.decode(), ORIGIN)

    @override_settings(ALLOWED_HOSTS=[ORIGIN])
    def test_forwarded_host_also_requires_allowed_hosts_membership(self):
        request = RequestFactory().get('/', HTTP_HOST=ORIGIN, HTTP_X_FH_REQUESTED_HOST=HOSTS[0])
        response = NoStoreMiddleware(lambda r: HttpResponse(r.get_host()))(request)
        self.assertEqual(response.content.decode(), ORIGIN)


@override_settings(
    ALLOWED_HOSTS=[ORIGIN, *HOSTS], CSRF_TRUSTED_ORIGINS=['https://' + h for h in HOSTS],
    SESSION_COOKIE_NAME='__session', SESSION_COOKIE_SECURE=True, SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax', CSRF_USE_SESSIONS=True, SECURE_SSL_REDIRECT=True,
    SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO', 'https'), PUBLIC_API_CACHE_TTL=300,
    MIDDLEWARE=[
        'django.middleware.security.SecurityMiddleware',
        'whitenoise.middleware.WhiteNoiseMiddleware',
        'fathaker.middleware.NoStoreMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
    ],
)
class ProductionDomainTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        NavLink.objects.create(name='radios_list', display_name='Radio', destination='radio:radios_list')
        cls.radio = Radio.objects.create(name='إذاعة القرآن', rank=1, image='radio/original.png')
        User.objects.create_superuser('domain-test', 'test@example.test', 'local-only-test-password')

    def client_for(self, host):
        return Client(enforce_csrf_checks=True, HTTP_HOST=ORIGIN,
                      HTTP_X_FORWARDED_HOST=host, HTTP_X_FORWARDED_PROTO='https')

    def test_open_graph_share_urls_and_redirects(self):
        for host in HOSTS:
            with self.subTest(host=host):
                client = self.client_for(host)
                response = client.get('/')
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response['Location'], '/radio/')
                response = client.get('/radio/')
                self.assertContains(response, f'<meta property="og:url" content="https://{host}/radio/">')
                self.assertContains(response, 'G-6NHQ4PT7XH')
                path = reverse('radio:radio_detail', kwargs={'slug': self.radio.slug})
                response = client.get(path)
                self.assertContains(response, f'https://{host}{path}')
                self.assertContains(response, f'<meta property="og:image" content="https://{host}/media/radio/original.png">')
                self.assertEqual(response['Cache-Control'], 'private, no-store')
                self.assertEqual(client.get('/admin').status_code, 301)

    def test_session_cookie_csrf_login_logout_and_protected_access(self):
        for host in HOSTS:
            with self.subTest(host=host):
                client = self.client_for(host)
                login = reverse('admin:login')
                response = client.get(login)
                token = str(response.context['csrf_token'])
                cookie = client.cookies['__session']
                self.assertTrue(cookie['secure']); self.assertTrue(cookie['httponly'])
                self.assertEqual(cookie['samesite'], 'Lax'); self.assertEqual(cookie['domain'], '')
                self.assertNotIn('csrftoken', client.cookies)
                credentials = {'username':'domain-test', 'password':'local-only-test-password'}
                self.assertEqual(client.post(login, credentials, HTTP_ORIGIN=f'https://{host}').status_code, 403)
                credentials['csrfmiddlewaretoken'] = token
                self.assertEqual(client.post(login, credentials, HTTP_ORIGIN='https://attacker.test').status_code, 403)
                response = client.post(login, credentials, HTTP_ORIGIN=f'https://{host}')
                self.assertEqual(response.status_code, 302)
                response = client.get(reverse('admin:index'))
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response['Cache-Control'], 'private, no-store')
                response = client.post(reverse('admin:logout'),
                    {'csrfmiddlewaretoken':str(response.context['csrf_token'])}, HTTP_ORIGIN=f'https://{host}')
                self.assertIn(response.status_code, [200,302])
                self.assertEqual(client.get(reverse('admin:index')).status_code, 302)

    def test_unauthorized_actual_host_is_rejected(self):
        client = Client(HTTP_HOST='attacker.test', HTTP_X_FORWARDED_HOST='attacker.test',
                        HTTP_X_FORWARDED_PROTO='https')
        self.assertEqual(client.get('/radio/').status_code, 400)
