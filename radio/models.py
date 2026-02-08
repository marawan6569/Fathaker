from django.db import models
from django.utils.text import slugify
from taggit.managers import TaggableManager
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _


class Radio(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("Radio Name"))
    stream_url = models.URLField(verbose_name=_("Radio Stream URL"))
    description = models.TextField(null=True, blank=True, verbose_name=_("Radio Description"))
    image = models.ImageField(upload_to="radio/", null=True, blank=True, verbose_name=_("Radio Image"))

    rank = models.IntegerField(unique=True, null=False, blank=False, verbose_name=_("Radio Rank"))
    likes_count = models.IntegerField(default=0, verbose_name=_("Likes Count"))
    views_count = models.IntegerField(default=0, verbose_name=_("Views Count"))
    slug = models.SlugField(max_length=150, unique=True, allow_unicode=True, blank=True, verbose_name=_("Slug"))

    tags = TaggableManager(blank=True)

    class Meta:
        ordering = ["rank"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name, allow_unicode=True)
            if not base_slug:
                base_slug = f"radio-{self.pk or 'new'}"
            slug = base_slug
            counter = 1
            while Radio.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def stream_link(self):
        return mark_safe(f"<a href='{self.stream_url}' target='_blank'>{self.stream_url}</a>")

    def __str__(self):
        return self.name

