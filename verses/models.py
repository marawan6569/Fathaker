from django.db import models
from django.utils.translation import gettext as _

# Create your models here.


class Surah(models.Model):
    name = models.CharField(max_length=50, verbose_name=_('Surah Name'))
    name_without_tashkeel = models.CharField(max_length=30, verbose_name=_('Surah Name Without Tashkeel'))

    class Meta:
        verbose_name = _('Surah')
        verbose_name_plural = _('Surahes')

    def __str__(self):
        return self.name


class Verse(models.Model):
    verse_pk = models.CharField(max_length=8, unique=True, verbose_name=_('Verse Primary Key'))
    page = models.PositiveIntegerField(verbose_name=_('Page'))
    the_quarter = models.PositiveIntegerField(verbose_name=_('The Quarter'))
    juz = models.PositiveIntegerField(verbose_name='Juz')
    surah = models.ForeignKey(Surah, on_delete=models.CASCADE, related_name='verses', verbose_name=_('Surah'))
    verse = models.CharField(max_length=5000, verbose_name=_('Verse'))
    verse_without_tashkeel = models.CharField(max_length=1000, verbose_name=_('Verse Without Tashkeel'))
    number_in_surah = models.PositiveIntegerField(verbose_name=_('Verse Number In Surah'))
    number_in_quran = models.PositiveIntegerField(unique=True, verbose_name=_('Verse Number In Quran'))
    is_sajda = models.BooleanField(verbose_name=_('Is the verse a sajda?'))

    class Meta:
        verbose_name = _('Verse')
        verbose_name_plural = _('Verses')

    def __str__(self):
        return self.verse[:50]
