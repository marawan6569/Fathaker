from django.db import models
from taggit.managers import TaggableManager
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
# Create your models here.


class Radio(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("Radio Name"))
    stream_url = models.URLField(verbose_name=_("Radio Stream URL"))
    description = models.TextField(null=True, blank=True, verbose_name=_("Radio Description"))
    image = models.ImageField(upload_to="radio/", null=True, blank=True, verbose_name=_("Radio Image"))

    rank = models.IntegerField(unique=True, null=False, blank=False, verbose_name=_("Radio Rank"))

    tags = TaggableManager()

    class Meta:
        ordering = ["rank"]

    def stream_link(self):
        return mark_safe(f"<a href='{self.stream_url}' target='_blank'>{self.stream_url}</a>")

    def __str__(self):
        return self.name

