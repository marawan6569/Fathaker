from django.test import TestCase
from .models import NavLink
# Create your tests here.


class NavLinkTest(TestCase):

    def setUp(self) -> None:
        home = NavLink.objects.create(link_type=0, name="home", display_name="home", destination="core:homepage")
        github = NavLink.objects.create(link_type=2, name="github", display_name="home",
                                        destination="https://github.com/", is_external=True)
        home.save()
        github.save()

    def test_nav_link__str__(self):
        home = NavLink.objects.get(name="home")
        github = NavLink.objects.get(name="github")
        self.assertEqual(home.__str__(), "home")
        self.assertEqual(github.__str__(), "github")

    def test_get_link(self):
        home = NavLink.objects.get(name="home")
        self.assertEqual(home.get_link(), "/")

    def test_get_link_if_is_external(self):
        github = NavLink.objects.get(name="github")
        self.assertEqual(github.get_link(), "https://github.com/")
