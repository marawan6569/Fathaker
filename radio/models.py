from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
# Create your models here.


class Category(models.Model):
    name = models.CharField(max_length=30)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def radios_count(self):
        return self.radios.count()

    def __str__(self):
        return self.name


class Radio(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("Radio Name"))
    stream_url = models.URLField(verbose_name=_("Radio Stream URL"))
    description = models.TextField(null=True, blank=True, verbose_name=_("Radio Description"))
    image = models.ImageField(upload_to="radio/", null=True, blank=True, verbose_name=_("Radio Image"))

    categories = models.ManyToManyField(Category, blank=True, related_name="radios", verbose_name=_("Radio Categories"))

    def stream_link(self):
        return mark_safe(f"<a href='{self.stream_url}' target='_blank'>{self.stream_url}</a>")

    def categories_list(self):
        return ", ".join([cat.name for cat in self.categories.all()])

    def __str__(self):
        return self.name
