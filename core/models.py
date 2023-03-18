from django.db import models
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
    path = models.CharField(max_length=100, verbose_name=_("Link path"))
    icon = models.CharField(max_length=100, verbose_name=_("FontAwesome Icon Class"))
    link_type = models.CharField(max_length=2, choices=links_types, verbose_name=_("Link Type"))
    is_active = models.BooleanField(default=True, verbose_name=_("Is Link Active ? "))

    def __str__(self):
        return self.name
