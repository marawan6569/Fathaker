from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Surah, Verse


# Create your tests here.

class SurahModelTest(TestCase):
    def setUp(self) -> None:
        surah = Surah.objects.create(name="الفاتحة", name_without_tashkeel="الْفَاتِحَة")

    def test_surah__str__(self):
        surah = Surah.objects.first()
        self.assertEqual(surah.__str__(), "الفاتحة")


class VerseModelTest(TestCase):

    def setUp(self) -> None:
        surah = Surah.objects.create(name="الفاتحة", name_without_tashkeel="الْفَاتِحَة")
        verse = Verse.objects.create(
            verse_pk="S001V001",
            page=1,
            the_quarter=1,
            juz=1,
            surah=surah,
            verse="بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
            verse_without_tashkeel="بسم الله الرحمن الرحيم",
            number_in_surah=1,
            number_in_quran=1,
            is_sajda=False,
        )

    def test_verse__str__(self):
        verse = Verse.objects.first()
        self.assertEqual(verse.__str__(), verse.verse[:50])


class VersesListAPITest(APITestCase):
    def setUp(self) -> None:
        surah_1 = Surah.objects.create(name="الْفَاتِحَة", name_without_tashkeel="الفاتحة")
        surah_2 = Surah.objects.create(name="الإخْلَاص", name_without_tashkeel="الأخلاص")
        verse_1 = Verse.objects.create(
            verse_pk="S001V001", page=1, the_quarter=1, juz=1, surah=surah_1,
            verse="بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ", verse_without_tashkeel="بسم الله الرحمن الرحيم",
            number_in_surah=1, number_in_quran=1, is_sajda=False,
        )
        verse_2 = Verse.objects.create(
            verse_pk="S112V001", page=604, the_quarter=240, juz=30, surah=surah_2,
            verse="قُلْ هُوَ اللَّهُ أَحَدٌ", verse_without_tashkeel="قل هو الله أحد",
            number_in_surah=1, number_in_quran=6222, is_sajda=False,
        )
        self.endpoint = reverse('verses:verses_list_api')

    def test_all_verses_list_api(self):
        data = {}
        response = self.client.get(self.endpoint, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_verses_in_page_api(self):
        data = {}
        response = self.client.get(self.endpoint + '?page=604', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class QuranMigrationSearchTests(TestCase):
    def setUp(self):
        surah = Surah.objects.create(name='الفاتحة', name_without_tashkeel='الفاتحة')
        self.verse = Verse.objects.create(
            verse_pk='S1V1', page=1, the_quarter=1, juz=1, surah=surah,
            verse='بِسْمِ اللَّهِ', verse_without_tashkeel='بسم الله',
            number_in_surah=1, number_in_quran=1, is_sajda=False,
        )

    def test_arabic_search_with_and_without_diacritics(self):
        cases = [
            ('verses_search_api', 'بِسْمِ'),
            ('verses_search_api', 'بسم'),
            ('verses_starts_with_api', 'بسم'),
            ('verses_ends_with_api', 'الله'),
        ]
        for endpoint, query in cases:
            with self.subTest(endpoint=endpoint, query=query):
                response = self.client.get(reverse('verses:' + endpoint), {'q': query})
                self.assertEqual(response.status_code, 200)
                self.assertEqual([v['verse_pk'] for v in response.json()], ['S1V1'])

    def test_mushaf_preserves_phrase_and_audio_relationships(self):
        from .models import Audio, Phrase, PhraseOccurrence
        audio = Audio.objects.create(url='https://example.test/recitation.mp3')
        self.verse.audio.add(audio)
        phrase = Phrase.objects.create(
            phrase_id=42, source_verse=self.verse, surahs_count=1, ayahs_count=1,
            occurrences_count=1, source_word_from=1, source_word_to=2,
        )
        PhraseOccurrence.objects.create(phrase=phrase, verse=self.verse, word_from=1, word_to=2)
        response = self.client.get(reverse('verses:mushaf_page_api'), {'page': 1})
        self.assertEqual(response.status_code, 200)
        verse = response.json()['verses'][0]
        self.assertEqual(verse['audio_url'], audio.url)
        self.assertEqual(verse['mutashabihat'][0]['phrase_id'], 42)
