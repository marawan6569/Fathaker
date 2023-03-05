from django.contrib import admin
from  .models import Verse, Surah

# Register your models here.


@admin.register(Verse)
class VerseAdmin(admin.ModelAdmin):

    list_display = ['__str__', 'verse_pk', 'surah', 'number_in_quran', 'page', 'the_quarter', 'juz', 'is_sajda']
    list_filter = ['surah', 'juz', 'the_quarter', 'page', 'is_sajda']
    search_fields = ['verse', 'verse_without_tashkeel']


@admin.register(Surah)
class SurahAdmin(admin.ModelAdmin):
    list_display = ['name', 'name_without_tashkeel']
    search_fields = ['name', 'name_without_tashkeel']
