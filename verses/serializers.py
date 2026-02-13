from rest_framework import serializers
from .models import Verse, Audio
from .mutashabihat import Phrase, PhraseOccurrence


class AudioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Audio
        fields = ['id', 'name', 'url']


class VerseSerializer(serializers.ModelSerializer):

    surah = serializers.StringRelatedField()
    audio = AudioSerializer(many=True, read_only=True)

    class Meta:
        model = Verse
        fields = [
            'verse_pk',
            'page',
            'the_quarter',
            'juz',
            'surah',
            'verse',
            'verse_without_tashkeel',
            'number_in_surah',
            'number_in_quran',
            'is_sajda',
            'audio',
        ]


class PhraseOccurrenceSerializer(serializers.ModelSerializer):
    verse = VerseSerializer(read_only=True)

    class Meta:
        model = PhraseOccurrence
        fields = ['id', 'verse', 'word_from', 'word_to']


class PhraseSerializer(serializers.ModelSerializer):
    source_verse = VerseSerializer(read_only=True)
    occurrences = PhraseOccurrenceSerializer(many=True, read_only=True)

    class Meta:
        model = Phrase
        fields = [
            'id', 'phrase_id', 'surahs_count', 'ayahs_count',
            'occurrences_count', 'source_verse',
            'source_word_from', 'source_word_to',
            'occurrences',
        ]

