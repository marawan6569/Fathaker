from django.test import TestCase
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
