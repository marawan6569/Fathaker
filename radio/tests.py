from django.db.models import Max
from django.test import TestCase, Client
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.contrib.auth.models import User
from core.models import NavLink
from .models import Category, Radio, RadioCategoriesM2M


# Create your tests here.


class CategoryModelTest(TestCase):

    def setUp(self) -> None:
        cat1 = Category.objects.create(name="CAT #1", rank=1)
        cat2 = Category.objects.create(name="CAT #2", rank=2)
        radio1 = Radio.objects.create(name="Radio #1", stream_url="https://fake.radio1.test")
        radio2 = Radio.objects.create(name="Radio #2", stream_url="https://fake.radio2.test")
        radio3 = Radio.objects.create(name="Radio #3", stream_url="https://fake.radio3.test")

        radio1.categories.add(cat1, through_defaults={'rank': 1})
        radio1.categories.add(cat2, through_defaults={'rank': 1})
        radio2.categories.add(cat1, through_defaults={'rank': 2})
        radio3.categories.add(cat1, through_defaults={'rank': 3})
        radio3.categories.add(cat2, through_defaults={'rank': 2})

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
        cat1 = Category.objects.create(name="CAT #1", rank=1)
        cat2 = Category.objects.create(name="CAT #2", rank=2)
        cat3 = Category.objects.create(name="CAT #3", rank=3)
        radio1 = Radio.objects.create(name="Radio #1", stream_url="https://fake.radio1.test")
        radio2 = Radio.objects.create(name="Radio #2", stream_url="https://fake.radio2.test")
        radio1.categories.add(cat1, through_defaults={'rank': 1})
        radio1.categories.add(cat2, through_defaults={'rank': 2})
        radio2.categories.add(cat3, through_defaults={'rank': 1})

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


class RadioCategoriesM2MModelTest(TestCase):

    def setUp(self) -> None:
        cat1 = Category.objects.create(name="CAT #1", rank=1)
        radio1 = Radio.objects.create(name="Radio #1", stream_url="https://fake.radio1.test")
        radio1.categories.add(cat1, through_defaults={'rank': 1})

    def test_radio_categories_m2m__str__(self):
        cat1 = Category.objects.get(name="CAT #1")
        rel = RadioCategoriesM2M.objects.get(category=cat1)
        self.assertEqual(rel.__str__(), "Radio #1")


class RadiosListViewTest(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        link = NavLink.objects.create(name="radios_list", display_name="radios_list")

    def test_radios_list_page(self):
        url = reverse("radio:radios_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'radio/radios_list.html')


class CategoryRankingViewsTest(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        cat1 = Category.objects.create(name="CAT #1", rank=1)
        cat2 = Category.objects.create(name="CAT #2", rank=2)
        cat3 = Category.objects.create(name="CAT #3", rank=3)
        self.username = "staff_user"
        self.password = "123"
        staff_user = User.objects.create(username="staff_user", is_staff=True, is_superuser=True)
        staff_user.set_password(self.password)
        staff_user.save()

    def test_category_rank_up(self):
        cat3 = Category.objects.get(rank=3)
        url = reverse("radio:category_rank_up", args=[cat3.id])

        request = self.client
        request.login(username=self.username, password=self.password)
        response = request.get(url, follow=True)

        self.assertRedirects(response, "/admin/radio/category/", status_code=302,
                             target_status_code=200, fetch_redirect_response=True)

    def test_category_rank_down(self):
        cat1 = Category.objects.get(rank=1)
        url = reverse("radio:category_rank_down", args=[cat1.id])

        request = self.client
        request.login(username=self.username, password=self.password)
        response = request.get(url, follow=True)

        self.assertRedirects(response, "/admin/radio/category/", status_code=302,
                             target_status_code=200, fetch_redirect_response=True)


class RadioRankingInCategoryViewsTest(TestCase):

    @staticmethod
    def get_next_rank(category):
        max_rank = RadioCategoriesM2M.objects.filter(category=category).aggregate(Max('rank'))
        return max_rank['rank__max'] + 1 if max_rank['rank__max'] else 1

    def setUp(self) -> None:
        self.client = Client()
        cat1 = Category.objects.create(name="CAT #1", rank=1)

        radio1 = Radio.objects.create(name="Radio #1", stream_url="https://fake.radio1.test")
        radio1.categories.add(cat1, through_defaults={'rank': self.get_next_rank(cat1)})

        radio2 = Radio.objects.create(name="Radio #1", stream_url="https://fake.radio1.test")
        radio2.categories.add(cat1, through_defaults={'rank': self.get_next_rank(cat1)})

        radio3 = Radio.objects.create(name="Radio #1", stream_url="https://fake.radio1.test")
        radio3.categories.add(cat1, through_defaults={'rank': self.get_next_rank(cat1)})

        self.username = "staff_user"
        self.password = "123"
        staff_user = User.objects.create(username="staff_user", is_staff=True, is_superuser=True)
        staff_user.set_password(self.password)
        staff_user.save()

    def test_radio_rank_in_category_up(self):
        rel = RadioCategoriesM2M.objects.get(rank=2)
        url = reverse("radio:radio_rank_in_category_up", args=[rel.id])

        request = self.client
        request.login(username=self.username, password=self.password)
        response = request.get(url, follow=True)

        self.assertRedirects(response, "/admin/radio/radiocategoriesm2m/", status_code=302,
                             target_status_code=200, fetch_redirect_response=True)

    def test_radio_rank_in_category_down(self):
        rel = RadioCategoriesM2M.objects.get(rank=2)
        url = reverse("radio:radio_rank_in_category_down", args=[rel.id])

        request = self.client
        request.login(username=self.username, password=self.password)
        response = request.get(url, follow=True)

        self.assertRedirects(response, "/admin/radio/radiocategoriesm2m/", status_code=302,
                             target_status_code=200, fetch_redirect_response=True)
