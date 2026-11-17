from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import resolve, reverse

from core.models import NavLink
from radio.models import Radio
from verses.models import Surah, Verse, Audio, Phrase, PhraseOccurrence
from .middleware import NoStoreMiddleware


@override_settings(PUBLIC_API_CACHE_TTL=300)
class CachePolicyTests(SimpleTestCase):
    def apply(self, path='/verses/api/mushaf-page/?page=1', response=None, method='get', **headers):
        request = getattr(RequestFactory(), method)(path, **headers)
        request.resolver_match = resolve(request.path)
        request.user = AnonymousUser()
        response = JsonResponse({'public': True}) if response is None else response
        return NoStoreMiddleware(lambda r: response)(request)

    def assert_private(self, response):
        self.assertEqual(response['Cache-Control'], 'private, no-store')

    def test_only_explicit_json_endpoints_and_bounded_ranges(self):
        for path in ['/verses/api/mushaf-page/', '/verses/api/mushaf-page/?page=604',
                     '/verses/api/verse/1/1/', '/verses/api/surah/1/',
                     '/verses/api/range/100/1/', '/verses/api/mutashabihat/phrase/1/',
                     '/verses/api/mutashabihat/by-ayah/?ayah=S2V23']:
            with self.subTest(path=path):
                response = self.apply(path)
                self.assertEqual(response['Cache-Control'], 'public, max-age=0, s-maxage=300')
                self.assertEqual(set(response['Vary'].lower().split(', ')), {'accept','authorization','cookie'})
        for path in ['/verses/api/search/?q=الله', '/verses/api/verses_list',
                     '/verses/api/starts-with/?q=بسم', '/verses/api/ends-with/?q=الله',
                     '/verses/api/mutashabihat/search/?q=الله', '/radio/', '/admin/login/',
                     '/verses/api/range/1/101/', '/verses/api/surah/1/?q=الله',
                     '/verses/api/mushaf-page/?page=0','/verses/api/mushaf-page/?page=bad',
                     '/verses/api/mushaf-page/?page=1&page=2',
                     '/verses/api/mushaf-page/?page=1&unknown=1',
                     '/verses/api/verse/1/1/?format=api']:
            with self.subTest(path=path):
                self.assert_private(self.apply(path))

    def test_methods_cookies_authorization(self):
        self.assertIn('public', self.apply(method='head')['Cache-Control'])
        for method in ['post','put','patch','delete','options']:
            self.assert_private(self.apply(method=method))
        for header in [{'HTTP_COOKIE':'__session=existing'}, {'HTTP_COOKIE':'sessionid=existing'},
                       {'HTTP_COOKIE':'tracking=1'}, {'HTTP_AUTHORIZATION':'Bearer anything'},
                       {'HTTP_AUTHORIZATION':''}]:
            self.assert_private(self.apply(**header))

    def test_response_guards(self):
        cookie = JsonResponse({'public': True});cookie.set_cookie('__session','test')
        cookie_header = JsonResponse({'public': True});cookie_header['Set-Cookie']='test=1'
        private = JsonResponse({'public': True});private['Cache-Control']='private'
        no_store = JsonResponse({'public': True});no_store['Cache-Control']='no-store'
        vary = JsonResponse({'public': True});vary['Vary']='*'
        attachment = JsonResponse({'public': True});attachment['Content-Disposition']='attachment'
        for response in [cookie,cookie_header,private,no_store,vary,attachment,
                         JsonResponse({'error':True},status=404),JsonResponse({'redirect':True},status=302),
                         HttpResponse('<input name="csrfmiddlewaretoken">'),
                         JsonResponse({'large':'x'*(1024*1024)}),StreamingHttpResponse(['{}'], content_type='application/json')]:
            self.assert_private(self.apply(response=response))

    @override_settings(PUBLIC_API_CACHE_TTL=0)
    def test_kill_switch(self):
        self.assert_private(self.apply())


@override_settings(PUBLIC_API_CACHE_TTL=300, MIDDLEWARE=[
    'fathaker.middleware.NoStoreMiddleware', *settings.MIDDLEWARE
])
class CacheEndpointTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        NavLink.objects.create(name='radios_list',display_name='Radio',destination='radio:radios_list')
        cls.radio=Radio.objects.create(name='إذاعة القرآن',rank=1)
        cls.user=User.objects.create_user('cache-user',password='local-test-only')
        surah=Surah.objects.create(name='الفاتحة',name_without_tashkeel='الفاتحة')
        for n in [1,2]:
            v=Verse.objects.create(verse_pk=f'S1V{n}',surah=surah,page=n,the_quarter=1,juz=1,
                verse='بِسْمِ اللَّهِ',verse_without_tashkeel='بسم الله',number_in_surah=n,number_in_quran=n,is_sajda=False)
            v.audio.add(Audio.objects.create(url=f'https://example.test/{n}.mp3'))
            phrase=Phrase.objects.create(phrase_id=n,source_verse=v,surahs_count=1,ayahs_count=1,
                occurrences_count=1,source_word_from=1,source_word_to=2)
            PhraseOccurrence.objects.create(phrase=phrase,verse=v,word_from=1,word_to=2)

    def test_distinct_parameters_and_exact_payload_when_disabled(self):
        endpoint=reverse('verses:mushaf_page_api')
        pages=[]
        for page in [1,2]:
            response=self.client.get(endpoint,{'page':page})
            self.assertIn('public',response['Cache-Control']);self.assertFalse(response.cookies)
            self.assertEqual(response.json()['verses'][0]['verse_pk'],f'S1V{page}')
            with override_settings(PUBLIC_API_CACHE_TTL=0):
                private=self.client.get(endpoint,{'page':page})
            self.assertEqual(response.content,private.content)
            self.assertEqual(private['Cache-Control'],'private, no-store')
            pages.append(response.content)
        self.assertNotEqual(*pages)
        for ayah in ['S1V1','S1V2']:
            response=self.client.get(reverse('verses:mutashabihat_by_ayah_api'),{'ayah':ayah})
            self.assertEqual(response.json()[0]['source_verse']['verse_pk'],ayah)
            self.assertIn('public',response['Cache-Control'])

    def test_anonymous_session_and_authenticated_are_private(self):
        endpoint=reverse('verses:mushaf_page_api')
        self.client.cookies['__session']='existing'
        self.assertEqual(self.client.get(endpoint)['Cache-Control'],'private, no-store')
        self.client.cookies.clear()
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(endpoint)['Cache-Control'],'private, no-store')

    def test_radio_counter_and_html_remain_private(self):
        response=self.client.get(reverse('radio:radio_detail',kwargs={'slug':self.radio.slug}))
        self.assertEqual(response['Cache-Control'],'private, no-store')
        self.radio.refresh_from_db();self.assertEqual(self.radio.views_count,1)
        response=self.client.post(reverse('radio:radio_like',kwargs={'slug':self.radio.slug}))
        self.assertEqual(response['Cache-Control'],'private, no-store')
        self.radio.refresh_from_db();self.assertEqual(self.radio.likes_count,1)


@override_settings(ALLOWED_HOSTS=['testserver', 'fathaker-quran.web.app'])
class HostingHostTests(SimpleTestCase):
    def test_only_exact_allowed_hosting_names_restore_public_urls(self):
        for forwarded, expected in [('fathaker-quran.web.app','fathaker-quran.web.app'),
                                    ('attacker.test','testserver'),
                                    ('fathaker-quran.web.app,attacker.test','testserver')]:
            request=RequestFactory().get('/radio/',HTTP_HOST='testserver',HTTP_X_FORWARDED_HOST=forwarded)
            response=NoStoreMiddleware(lambda r: HttpResponse(r.build_absolute_uri()))(request)
            self.assertIn('http://'+expected+'/',response.content.decode())
            self.assertEqual(response['Cache-Control'],'private, no-store')

    def test_authenticated_user_without_cookie_is_private(self):
        from types import SimpleNamespace
        with override_settings(PUBLIC_API_CACHE_TTL=300):
            request=RequestFactory().get('/verses/api/verse/1/1/')
            request.resolver_match=resolve(request.path)
            request.user=SimpleNamespace(is_authenticated=True)
            response=NoStoreMiddleware(lambda r: JsonResponse({'public':True}))(request)
            self.assertEqual(response['Cache-Control'],'private, no-store')
