from django.test import TestCase
from django.utils.safestring import mark_safe
from .models import Category, Radio


# Create your tests here.


class CategoryModelTest(TestCase):

    def setUp(self) -> None:
        cat1 = Category.objects.create(name="CAT #1")
        cat2 = Category.objects.create(name="CAT #2")
        radio1 = Radio.objects.create(name="Radio #1", stream_url="https://fake.radio1.test")
        radio2 = Radio.objects.create(name="Radio #2", stream_url="https://fake.radio2.test")
        radio3 = Radio.objects.create(name="Radio #3", stream_url="https://fake.radio3.test")

        radio1.categories.add(cat1)
        radio1.categories.add(cat2)
        radio1.save()

        radio2.categories.add(cat1)
        radio2.save()

        radio3.categories.add(cat1)
        radio3.categories.add(cat2)
        radio3.save()

    def test_radios_count(self):
        cat1 = Category.objects.get(name="CAT #1")
        cat2 = Category.objects.get(name="CAT #2")
        self.assertEqual(cat1.radios_count(), 3)
        self.assertEqual(cat2.radios_count(), 2)

    def test_category__str__(self):
        cat1 = Category.objects.get(name="CAT #1")
        cat2 = Category.objects.get(name="CAT #2")
        self.assertEqual(cat1.__str__(), "CAT #1")
        self.assertEqual(cat2.__str__(), "CAT #2")


class RadioModelTest(TestCase):

    def setUp(self) -> None:
        cat1 = Category.objects.create(name="CAT #1")
        cat2 = Category.objects.create(name="CAT #2")
        cat3 = Category.objects.create(name="CAT #3")
        radio1 = Radio.objects.create(name="Radio #1", stream_url="https://fake.radio1.test")
        radio2 = Radio.objects.create(name="Radio #2", stream_url="https://fake.radio2.test")

        radio1.categories.add(cat1)
        radio1.categories.add(cat2)
        radio1.save()

        radio2.categories.add(cat3)
        radio2.save()

    def test_radio_stream_link(self):
        radio1 = Radio.objects.get(name="Radio #1")
        radio2 = Radio.objects.get(name="Radio #2")
        self.assertEqual(
            radio1.stream_link(),
            mark_safe("<a href='https://fake.radio1.test' target='_blank'>https://fake.radio1.test</a>")
        )
        self.assertEqual(
            radio2.stream_link(),
            mark_safe("<a href='https://fake.radio2.test' target='_blank'>https://fake.radio2.test</a>")
        )

    def test_radio_categories_list(self):
        radio1 = Radio.objects.get(name="Radio #1")
        radio2 = Radio.objects.get(name="Radio #2")
        self.assertEqual(radio1.categories_list(), "CAT #1, CAT #2")
        self.assertEqual(radio2.categories_list(), "CAT #3")

    def test_radio__str__(self):
        radio1 = Radio.objects.get(name="Radio #1")
        radio2 = Radio.objects.get(name="Radio #2")
        self.assertEqual(radio1.__str__(), "Radio #1")
        self.assertEqual(radio2.__str__(), "Radio #2")
