"""Query budgets and reproducible synthetic request benchmarks on test databases only."""
import hashlib
import json
import os
import re
from time import perf_counter
from statistics import median

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from core.models import NavLink
from radio.models import Radio
from .models import Audio, Phrase, PhraseOccurrence, Surah, Verse
from .serializers import VerseSerializer, PhraseSerializer


def canonical_payload(value):
    """Compare unordered API collections without relying on database scan order.

    Radio ranks and mushaf verse order are checked separately.
    """
    if isinstance(value, dict):
        return {key: canonical_payload(item) for key, item in value.items()}
    if isinstance(value, list):
        return sorted((canonical_payload(item) for item in value),
                      key=lambda item: json.dumps(item, sort_keys=True, ensure_ascii=False))
    return value


class QueryPerformanceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        NavLink.objects.create(name='radios_list', display_name='Radio', destination='radio:radios_list')
        for i in range(163):
            radio = Radio.objects.create(name=f'إذاعة القرآن {i}', rank=163-i)
            radio.tags.add('قرآن', 'تلاوة "عربية"')
        surahs = [Surah.objects.create(name=f'سورة {i}', name_without_tashkeel=f'سورة {i}') for i in range(2)]
        verses = Verse.objects.bulk_create([
            Verse(verse_pk=f'S1V{i+1}', page=1 if i == 0 else 2, the_quarter=1,
                  juz=1, surah=surahs[i % 2], verse='بِسْمِ اللَّهِ',
                  verse_without_tashkeel='بسم الله', number_in_surah=i+1,
                  number_in_quran=i+1, is_sajda=False) for i in range(200)
        ])
        for i, verse in enumerate(verses):
            if i != 199:  # Also exercise an empty audio relationship.
                verse.audio.add(*Audio.objects.bulk_create([
                    Audio(name=f'قارئ {j}', url=f'https://example.test/{i}/{j}.mp3') for j in range(3)
                ]))
        for i in range(30):
            phrase = Phrase.objects.create(phrase_id=i+1, source_verse=verses[i],
                surahs_count=2, ayahs_count=20, occurrences_count=20,
                source_word_from=1, source_word_to=2)
            PhraseOccurrence.objects.bulk_create([
                PhraseOccurrence(phrase=phrase, verse=v, word_from=1, word_to=2)
                for v in [verses[0], *verses[1+i:20+i]]
            ])

    def measured_get(self, name, budget, params=None, kwargs=None):
        url = reverse(name, kwargs=kwargs)
        samples = []
        repeats = 3 if os.getenv('PERFORMANCE_REPORT') else 1
        for _ in range(repeats):
            sql_time = 0
            def timer(execute, sql, params, many, context):
                nonlocal sql_time
                start = perf_counter()
                try:
                    return execute(sql, params, many, context)
                finally:
                    sql_time += perf_counter() - start
            start = perf_counter()
            with connection.execute_wrapper(timer), CaptureQueriesContext(connection) as queries:
                response = self.client.get(url, params or {})
            elapsed = perf_counter() - start
            self.assertEqual(response.status_code, 200)
            if not os.getenv('PERFORMANCE_BASELINE'):
                self.assertLessEqual(len(queries), budget)
            samples.append((elapsed, sql_time, len(queries)))
        if os.getenv('PERFORMANCE_REPORT'):
            if response.headers['Content-Type'].startswith('application/json'):
                payload = json.dumps(canonical_payload(response.json()), ensure_ascii=False, sort_keys=True).encode()
            else:
                payload = re.sub(rb'csrfmiddlewaretoken[^>]+', b'csrfmiddlewaretoken', response.content)
                payload = re.sub(rb"const CSRF_TOKEN = '[^']*'", b"const CSRF_TOKEN = 'REDACTED'", payload)
            print('PERF', json.dumps(dict(endpoint=url, params=params, queries=samples[-1][2],
                response_ms=round(median(x[0] for x in samples)*1000, 2),
                sql_ms=round(median(x[1] for x in samples)*1000, 2),
                sha256=hashlib.sha256(payload).hexdigest())))
        return response

    def test_radio_listing(self):
        response = self.measured_get('radio:radios_list', 6)
        radios = list(response.context['radios'])
        self.assertEqual([r.rank for r in radios], list(range(1, 164)))
        self.assertContains(response, 'قرآن')
        self.assertContains(response, r'تلاوة \u0022عربية\u0022')

    def test_verse_endpoints(self):
        expected = VerseSerializer(Verse.objects.all(), many=True).data
        cases = [
            ('verses_list_api', {}, None, expected),
            ('verses_list_api', {'page': 1}, None, expected[:1]),
            ('verses_search_api', {'q': 'بسم'}, None, expected),
            ('verses_search_api', {'q': 'بِسْمِ'}, None, expected),
            ('verses_starts_with_api', {'q': 'بسم'}, None, expected),
            ('verses_ends_with_api', {'q': 'الله'}, None, expected),
            ('surah_verses_api', {}, {'surah_id': 1}, expected),
            ('verses_range_api', {}, {'start': 200, 'end': 1}, expected),
            ('verse_detail_api', {}, {'surah_id': 1, 'verse_number': 1}, expected[0]),
        ]
        for name, params, kwargs, data in cases:
            with self.subTest(endpoint=name, params=params):
                response = self.measured_get('verses:'+name, 2, params, kwargs)
                self.assertEqual(canonical_payload(response.json()), canonical_payload(data))
                if not os.getenv('PERFORMANCE_BASELINE'):
                    verses = response.json() if isinstance(response.json(), list) else [response.json()]
                    numbers = [v['number_in_quran'] for v in verses]
                    self.assertEqual(numbers, sorted(numbers))
                    for verse in verses:
                        ids = [audio['id'] for audio in verse['audio']]
                        self.assertEqual(ids, sorted(ids))

    def test_phrases(self):
        expected = PhraseSerializer(Phrase.objects.all(), many=True).data
        for name, params, kwargs, data in [
            ('mutashabihat_search_api', {'q': 'بسم'}, None, expected),
            ('mutashabihat_search_api', {'q': 'بِسْمِ'}, None, expected),
            ('mutashabihat_by_ayah_api', {'ayah': 'S1V1'}, None, expected),
            ('mutashabihat_phrase_detail_api', {}, {'phrase_id': 1}, expected[0]),
        ]:
            with self.subTest(endpoint=name):
                response = self.measured_get('verses:'+name, 4, params, kwargs)
                self.assertEqual(canonical_payload(response.json()), canonical_payload(data))

    def test_mushaf(self):
        for page, count in [(1, 1), (2, 199), (604, 0)]:
            response = self.measured_get('verses:mushaf_page_api', 3, {'page': page})
            self.assertEqual(len(response.json()['verses']), count)
            numbers = [v['number_in_quran'] for v in response.json()['verses']]
            self.assertEqual(numbers, sorted(numbers))
            if page == 1:
                self.assertEqual(len(response.json()['verses'][0]['mutashabihat']), 30)

    def test_empty_and_missing(self):
        for name in ['verses_search_api', 'verses_starts_with_api', 'verses_ends_with_api']:
            self.assertEqual(self.measured_get('verses:'+name, 0).json(), [])
            self.assertEqual(self.measured_get('verses:'+name, 1, {'q': 'missing'}).json(), [])
        for name in ['mutashabihat_search_api', 'mutashabihat_by_ayah_api']:
            self.assertEqual(self.client.get(reverse('verses:'+name)).status_code, 400)
        self.assertEqual(self.client.get(reverse('verses:mutashabihat_phrase_detail_api', kwargs={'phrase_id': 999})).status_code, 404)
