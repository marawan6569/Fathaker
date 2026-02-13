from django.db import models
from django.utils.translation import gettext as _


class Phrase(models.Model):
    phrase_id = models.IntegerField(unique=True, verbose_name=_('Phrase ID'))
    surahs_count = models.IntegerField(verbose_name=_('Surahs Count'))
    ayahs_count = models.IntegerField(verbose_name=_('Ayahs Count'))
    occurrences_count = models.IntegerField(verbose_name=_('Occurrences Count'))
    source_verse = models.ForeignKey(
        'Verse', on_delete=models.CASCADE,
        related_name='source_phrases',
        verbose_name=_('Source Verse'),
    )
    source_word_from = models.IntegerField(verbose_name=_('Source Word From'))
    source_word_to = models.IntegerField(verbose_name=_('Source Word To'))

    class Meta:
        verbose_name = _('Phrase')
        verbose_name_plural = _('Phrases')

    def __str__(self):
        return f'Phrase {self.phrase_id}'


class PhraseOccurrence(models.Model):
    phrase = models.ForeignKey(
        Phrase, on_delete=models.CASCADE,
        related_name='occurrences',
        verbose_name=_('Phrase'),
    )
    verse = models.ForeignKey(
        'Verse', on_delete=models.CASCADE,
        related_name='phrase_occurrences',
        verbose_name=_('Verse'),
    )
    word_from = models.IntegerField(verbose_name=_('Word From'))
    word_to = models.IntegerField(verbose_name=_('Word To'))

    class Meta:
        verbose_name = _('Phrase Occurrence')
        verbose_name_plural = _('Phrase Occurrences')

    def __str__(self):
        return f'Phrase {self.phrase.phrase_id} in {self.verse.verse_pk}'
