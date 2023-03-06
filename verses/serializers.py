from rest_framework import serializers
from .models import Verse


class VerseSerializer(serializers.ModelSerializer):

    surah = serializers.StringRelatedField()

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
        ]
