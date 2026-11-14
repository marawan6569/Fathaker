"""Relationship loading plans for the nested public API serializers."""
from django.db.models import Prefetch

from .models import Audio, Verse
from .mutashabihat import Phrase, PhraseOccurrence


def serialized_verses():
    return Verse.objects.select_related('surah').prefetch_related(
        Prefetch('audio', queryset=Audio.objects.order_by('pk'))
    ).order_by('number_in_quran')


def serialized_phrases():
    return Phrase.objects.select_related('source_verse__surah').prefetch_related(
        Prefetch('source_verse__audio', queryset=Audio.objects.order_by('pk')),
        Prefetch(
            'occurrences',
            queryset=PhraseOccurrence.objects.select_related('verse__surah').prefetch_related(
                Prefetch('verse__audio', queryset=Audio.objects.order_by('pk'))
            ),
        ),
    )
