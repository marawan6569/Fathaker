from django.contrib.auth.models import User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import Client
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils.safestring import mark_safe

from core.models import NavLink
from .models import Radio
from .views import RadioRankUp, RadioRankDown


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


class RadioRankUpViewTest(TestCase):
    def setUp(self):
        # set the client
        self.client = Client()

        # Create a test user with admin privileges
        self.user = User.objects.create_user(username='admin', password='Aa@112244')
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()

        # Create test data: Radios with ranks
        self.radio1 = Radio.objects.create(name="Radio 1", rank=1)
        self.radio2 = Radio.objects.create(name="Radio 2", rank=2)
        self.radio3 = Radio.objects.create(name="Radio 3", rank=3)

    def test_radio_rank_up_if_user_is_not_authenticated(self):
        response = self.client.get(reverse('admin:radio_radio_changelist'))
        # print(response)
        self.assertEqual(response.status_code, 302)

    def test_radio_rank_up_if_user_is_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('admin:radio_radio_changelist'))
        self.assertEqual(response.status_code, 200)

    def test_radio_rank_up_if_radio_rank_is_not_first_rank(self):
        # Mock request
        request = RequestFactory().get(reverse('admin:radio_radio_changelist'))
        request.user = self.user
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        # Initialize SessionMiddleware with get_response argument
        middleware = SessionMiddleware(get_response=lambda r: None)
        middleware.process_request(request)
        request.session.save()

        # Mock view
        view = RadioRankUp.as_view()
        response = view(request, id=self.radio2.id)

        # Check if rank changed successfully
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Radio.objects.get(id=self.radio2.id).rank, 1)

    def test_radio_rank_up_if_radio_rank_is_first_rank(self):
        # Mock request
        request = RequestFactory().get(reverse('admin:radio_radio_changelist'))
        request.user = self.user
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        # Initialize SessionMiddleware with get_response argument
        middleware = SessionMiddleware(get_response=lambda r: None)
        middleware.process_request(request)
        request.session.save()

        # Mock view
        view = RadioRankUp.as_view()
        response = view(request, id=self.radio1.id)

        # Check if rank changed successfully
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Radio.objects.get(id=self.radio1.id).rank, 1)


class RadioRankDownViewTest(TestCase):
    def setUp(self):
        # set the client
        self.client = Client()

        # Create a test user with admin privileges
        self.user = User.objects.create_user(username='admin', password='Aa@112244')
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()

        # Create test data: Radios with ranks
        self.radio1 = Radio.objects.create(name="Radio 1", rank=1)
        self.radio2 = Radio.objects.create(name="Radio 2", rank=2)
        self.radio3 = Radio.objects.create(name="Radio 3", rank=3)

    def test_radio_rank_down_if_user_is_not_authenticated(self):
        response = self.client.get(reverse('admin:radio_radio_changelist'))
        # print(response)
        self.assertEqual(response.status_code, 302)

    def test_radio_rank_down_if_user_is_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('admin:radio_radio_changelist'))
        self.assertEqual(response.status_code, 200)

    def test_radio_rank_down_if_radio_rank_is_not_first_rank(self):
        # Mock request
        request = RequestFactory().get(reverse('admin:radio_radio_changelist'))
        request.user = self.user
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        # Initialize SessionMiddleware with get_response argument
        middleware = SessionMiddleware(get_response=lambda r: None)
        middleware.process_request(request)
        request.session.save()

        # Mock view
        view = RadioRankDown.as_view()
        response = view(request, id=self.radio2.id)

        # Check if rank changed successfully
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Radio.objects.get(id=self.radio2.id).rank, 3)

    def test_radio_rank_down_if_radio_rank_is_first_rank(self):
        # Mock request
        request = RequestFactory().get(reverse('admin:radio_radio_changelist'))
        request.user = self.user
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        # Initialize SessionMiddleware with get_response argument
        middleware = SessionMiddleware(get_response=lambda r: None)
        middleware.process_request(request)
        request.session.save()

        # Mock view
        view = RadioRankDown.as_view()
        response = view(request, id=self.radio3.id)

        # Check if rank changed successfully
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Radio.objects.get(id=self.radio3.id).rank, 3)
