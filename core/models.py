from django.db import models
from django.urls import reverse
from django.utils.translation import gettext as _


# Create your models here.


class NavLink(models.Model):
    links_types = (
        ("0", "Navbar"),
        ("1", "Footer Links"),
        ("2", "Footer Social"),
    )
    name = models.CharField(max_length=100, unique=True, verbose_name=_("Link Name (In Database)"))
    display_name = models.CharField(max_length=100, verbose_name=_("Link Name"))
    destination = models.CharField(max_length=100, verbose_name=_("Destination (View Name or External link)"))
    icon = models.CharField(max_length=100, null=True, blank=True, verbose_name=_("FontAwesome Icon Class"))
    link_type = models.CharField(max_length=2, choices=links_types, verbose_name=_("Link Type"))
    is_active = models.BooleanField(default=True, verbose_name=_("Is Link Active ? "))
    is_external = models.BooleanField(default=False, verbose_name=_("Is Link External Link ? "))

    def get_link(self):
        if self.is_external:
            return self.destination
        else:
            return reverse(self.destination)

    def __str__(self):
        return self.name
