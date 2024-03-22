from django.db.models import Max
from django.test import TestCase, Client
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.contrib.auth.models import User
from core.models import NavLink
from .models import Radio


# Create your tests here.

class RadioModelTest(TestCase):

    def setUp(self) -> None:
        radio1 = Radio.objects.create(name="Radio #1", stream_url="https://fake.radio1.test", rank=1)
        radio2 = Radio.objects.create(name="Radio #2", stream_url="https://fake.radio2.test", rank=2)

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

    def test_radio__str__(self):
        radio1 = Radio.objects.get(name="Radio #1")
        radio2 = Radio.objects.get(name="Radio #2")
        self.assertEqual(radio1.__str__(), "Radio #1")
        self.assertEqual(radio2.__str__(), "Radio #2")


class RadiosListViewTest(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        link = NavLink.objects.create(name="radios_list", display_name="radios_list")

    def test_radios_list_page(self):
        url = reverse("radio:radios_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'radio/radios_list.html')

