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
