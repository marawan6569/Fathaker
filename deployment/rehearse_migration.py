"""Synthetic SQLite -> empty local PostgreSQL rehearsal; never reads production.

Usage (activate the project virtualenv first):
  REHEARSAL_DATABASE_URL=postgresql://...@127.0.0.1:PORT/fathaker_rehearsal \
    python deployment/rehearse_migration.py

Only accepts a loopback PostgreSQL database named fathaker_rehearsal, with no public
schema tables. Creates data and leaves that disposable database for inspection.
Temporary SQLite/JSON artifacts are removed automatically.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from urllib.parse import urlparse

import psycopg

ROOT = Path(__file__).resolve().parent.parent
SEED = '''
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.models import LogEntry, ADDITION
from core.models import NavLink
from radio.models import Radio
from verses.models import Surah, Verse, Audio, Phrase, PhraseOccurrence
u = User.objects.create_superuser(id=101, username='rehearsal-admin', password='synthetic-only')
g = Group.objects.create(id=102, name='Editors')
p = Permission.objects.create(codename='custom_radio', name='Custom radio permission', content_type=ContentType.objects.get_for_model(Radio))
g.permissions.add(p)
u.groups.add(g)
u.user_permissions.add(p)
NavLink.objects.create(id=103, name='radios_list', display_name='إذاعات', destination='radio:radios_list')
r = Radio.objects.create(id=104, name='إذاعة القرآن', rank=1, image='radio/صورة.jpg', stream_url='https://example.test/radio', likes_count=3, views_count=8)
r.tags.add('قرآن', 'مباشر')
s = Surah.objects.create(id=105, name='الفاتحة', name_without_tashkeel='الفاتحة')
v = Verse.objects.create(id=106, surah=s, verse_pk='S1V1', page=1, the_quarter=1, juz=1, verse='بِسْمِ اللَّهِ', verse_without_tashkeel='بسم الله', number_in_surah=1, number_in_quran=1, is_sajda=False)
a = Audio.objects.create(id=107, name='تلاوة', url='https://example.test/verse.mp3')
v.audio.add(a)
p = Phrase.objects.create(id=108, phrase_id=42, source_verse=v, surahs_count=1, ayahs_count=1, occurrences_count=1, source_word_from=1, source_word_to=2)
PhraseOccurrence.objects.create(id=109, phrase=p, verse=v, word_from=1, word_to=2)
LogEntry.objects.create(user=u, content_type=ContentType.objects.get_for_model(r), object_id=str(r.pk), object_repr=r.name, action_flag=ADDITION)
'''
VERIFY = '''
from django.apps import apps
from django.contrib.auth.models import User
from django.db import connection
from radio.models import Radio
from verses.models import Verse
r = Radio.objects.get(pk=104)
assert r.image.name == 'radio/صورة.jpg'
assert set(r.tags.values_list('name', flat=True)) == {'قرآن', 'مباشر'}
u = User.objects.get(pk=101)
assert u.check_password('synthetic-only')
assert u.groups.get().permissions.filter(codename='custom_radio').exists()
assert u.user_permissions.filter(codename='custom_radio').exists()
v = Verse.objects.get(pk=106)
assert v.surah_id == 105 and v.audio.get().pk == 107
assert v.phrase_occurrences.get().phrase_id == 108
assert Verse.objects.filter(verse_without_tashkeel__icontains='بسم').get().pk == 106
# Exercise every populated integer PK sequence, including automatic M2M tables.
# This only advances sequences in the disposable database, without inserting rows.
with connection.cursor() as cursor:
    for model in apps.get_models(include_auto_created=True):
        if model._meta.pk.get_internal_type() not in ('AutoField', 'BigAutoField', 'SmallAutoField'):
            continue
        table, column = model._meta.db_table, model._meta.pk.column
        quote = connection.ops.quote_name
        cursor.execute(f'SELECT MAX({quote(column)}) FROM {quote(table)}')
        maximum = cursor.fetchone()[0]
        if maximum is None:
            continue
        cursor.execute('SELECT nextval(pg_get_serial_sequence(%s, %s))', [table, column])
        assert cursor.fetchone()[0] > maximum, table
r2 = Radio.objects.create(name='إذاعة جديدة', rank=2)
assert r2.pk > 104
'''


def main():
    url = os.environ.get('REHEARSAL_DATABASE_URL', '')
    parsed = urlparse(url)
    if (parsed.scheme not in ('postgres', 'postgresql')
            or parsed.hostname not in ('localhost', '127.0.0.1', '::1')
            or parsed.path != '/fathaker_rehearsal' or parsed.query or parsed.fragment):
        raise SystemExit('Set REHEARSAL_DATABASE_URL to a fresh loopback PostgreSQL database named fathaker_rehearsal (no query options).')
    with psycopg.connect(url) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'")
            if cursor.fetchone()[0]:
                raise SystemExit('Refusing a nonempty database. Create a new disposable database first.')

    env = {**os.environ, 'K_SERVICE': '', 'DEBLOYED': '0', 'DEBUG': '0', 'DATABASE_URL': ''}

    def command(environment, *args):
        subprocess.run([sys.executable, str(ROOT / 'manage.py'), *args],
                       cwd=ROOT, env=environment, check=True, stdout=subprocess.DEVNULL)

    with tempfile.TemporaryDirectory(prefix='fathaker-rehearsal-') as folder:
        source = {**env, 'SQLITE_PATH': str(Path(folder) / 'source.sqlite3')}
        target = {**env, 'DATABASE_URL': url}
        fixture = str(Path(folder) / 'migration.json')
        permissions = str(Path(folder) / 'permissions.json')
        restored = str(Path(folder) / 'restored.json')
        dump_args = ('dumpdata', '--all', '--natural-foreign', '--exclude', 'contenttypes',
                     '--exclude', 'auth.permission', '--exclude', 'sessions.session')
        command(source, 'migrate', '--noinput')
        command(source, 'shell', '-c', SEED)
        command(source, *dump_args, '--output', fixture)
        command(source, 'dumpdata', 'auth.permission', '--all', '--natural-foreign',
                '--natural-primary', '--output', permissions)
        command(target, 'migrate', '--noinput')
        command(target, 'loaddata', permissions, fixture)
        command(target, *dump_args, '--output', restored)
        original = json.loads(Path(fixture).read_text())
        result = json.loads(Path(restored).read_text())
        canonical = lambda rows: sorted(rows, key=lambda row: (row['model'], str(row['pk'])))
        assert canonical(original) == canonical(result), 'Source and target fixtures differ'
        labels = {row['model'] for row in original}
        assert {'verses.phrase', 'verses.phraseoccurrence', 'taggit.taggeditem'} <= labels
        command(target, 'shell', '-c', VERIFY)
        print(f'PASS: {len(original)} synthetic records across {len(labels)} models; '
              'exact fixture equality, Arabic content, custom permissions, relationships, '
              'password hashes, relative media keys, and PostgreSQL sequences verified.')


if __name__ == '__main__':
    main()
