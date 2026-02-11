from rest_framework import serializers
from .models import Verse, Audio


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
