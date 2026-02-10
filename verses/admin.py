from django.contrib import admin
from django.utils.safestring import mark_safe

from  .models import Verse, Surah

# Register your models here.


@admin.register(Verse)
class VerseAdmin(admin.ModelAdmin):

    list_display = ['__str__', 'verse_pk', 'surah', 'number_in_quran', 'page', 'the_quarter', 'juz', 'is_sajda']
    list_filter = ['surah', 'juz', 'the_quarter', 'page', 'is_sajda']
    search_fields = ['verse', 'verse_without_tashkeel']
    readonly_fields = ['preview_audio']

    def preview_audio(self, obj):
        style = "display: flex; flex-direction: row; flex-wrap: wrap; justify-content: center; align-items: center; gap: 10px;"
        return mark_safe("<br>".join(f'<dev style="{style}"><b>{audio.name}:</b> <audio controls><source src="{audio.url}" type="audio/mpeg"></audio></dev>' for audio in obj.audio.all()))


@admin.register(Surah)
class SurahAdmin(admin.ModelAdmin):
    list_display = ['name', 'name_without_tashkeel']
    search_fields = ['name', 'name_without_tashkeel']
