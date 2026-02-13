import json
import os

from django.core.management.base import BaseCommand
from verses.models import Verse
from verses.mutashabihat import Phrase, PhraseOccurrence


def ayah_key_to_verse_pk(ayah_key):
    """Convert '2:23' → 'S2V23'"""
    surah, verse = ayah_key.split(':')
    return f'S{surah}V{verse}'


class Command(BaseCommand):
    help = 'Import mutashabihat phrase data from phrases.json'

    def handle(self, *args, **options):
        json_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
            'phrases.json',
        )

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Pre-fetch all verses keyed by verse_pk for fast lookup
        verse_map = {v.verse_pk: v for v in Verse.objects.all()}

        # Clear existing data
        PhraseOccurrence.objects.all().delete()
        Phrase.objects.all().delete()

        phrases_created = 0
        occurrences_created = 0
        skipped = 0

        for phrase_id_str, phrase_data in data.items():
            phrase_id = int(phrase_id_str)
            source = phrase_data['source']
            source_vpk = ayah_key_to_verse_pk(source['key'])

            if source_vpk not in verse_map:
                self.stderr.write(f'Skipping phrase {phrase_id}: source verse {source_vpk} not found')
                skipped += 1
                continue

            phrase = Phrase.objects.create(
                phrase_id=phrase_id,
                surahs_count=phrase_data['surahs'],
                ayahs_count=phrase_data['ayahs'],
                occurrences_count=phrase_data['count'],
                source_verse=verse_map[source_vpk],
                source_word_from=source['from'],
                source_word_to=source['to'],
            )
            phrases_created += 1

            # Create occurrences from the 'ayah' dict
            occurrence_objects = []
            for ayah_key, word_ranges in phrase_data['ayah'].items():
                vpk = ayah_key_to_verse_pk(ayah_key)
                if vpk not in verse_map:
                    self.stderr.write(f'  Skipping occurrence: verse {vpk} not found')
                    skipped += 1
                    continue

                for word_range in word_ranges:
                    occurrence_objects.append(PhraseOccurrence(
                        phrase=phrase,
                        verse=verse_map[vpk],
                        word_from=word_range[0],
                        word_to=word_range[1],
                    ))

            PhraseOccurrence.objects.bulk_create(occurrence_objects)
            occurrences_created += len(occurrence_objects)

        self.stdout.write(self.style.SUCCESS(
            f'Done! Created {phrases_created} phrases, {occurrences_created} occurrences. Skipped {skipped}.'
        ))
