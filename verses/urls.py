from django.urls import path
from .api_views import (
    VersesList, VersesSearch, SurahVerses, VerseDetail,
    VersesRange, VersesStartsWith, VersesEndsWith,
)

app_name = 'verses'


urlpatterns = [

    # --> API <--
    path('api/verses_list', VersesList.as_view(), name='verses_list_api'),
    path('api/search/', VersesSearch.as_view(), name='verses_search_api'),
    path('api/surah/<int:surah_id>/', SurahVerses.as_view(), name='surah_verses_api'),
    path('api/verse/<int:surah_id>/<int:verse_number>/', VerseDetail.as_view(), name='verse_detail_api'),
    path('api/range/<int:start>/<int:end>/', VersesRange.as_view(), name='verses_range_api'),
    path('api/starts-with/', VersesStartsWith.as_view(), name='verses_starts_with_api'),
    path('api/ends-with/', VersesEndsWith.as_view(), name='verses_ends_with_api'),
]
