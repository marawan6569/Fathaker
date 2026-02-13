from django.urls import path
from .api_views import (
    VersesList, VersesSearch, SurahVerses, VerseDetail,
    VersesRange, VersesStartsWith, VersesEndsWith,
    MushafPageAPI,
    MutashabihatByAyah, MutashabihatSearch, MutashabihatPhraseDetail,
)
from .views import QuranSearch, QuranMushaf

app_name = 'verses'


urlpatterns = [

    # --> Pages <--
    path('search/', QuranSearch.as_view(), name='quran_search'),
    path('mushaf/', QuranMushaf.as_view(), name='quran_mushaf'),

    # --> API <--
    path('api/verses_list', VersesList.as_view(), name='verses_list_api'),
    path('api/search/', VersesSearch.as_view(), name='verses_search_api'),
    path('api/surah/<int:surah_id>/', SurahVerses.as_view(), name='surah_verses_api'),
    path('api/verse/<int:surah_id>/<int:verse_number>/', VerseDetail.as_view(), name='verse_detail_api'),
    path('api/range/<int:start>/<int:end>/', VersesRange.as_view(), name='verses_range_api'),
    path('api/starts-with/', VersesStartsWith.as_view(), name='verses_starts_with_api'),
    path('api/ends-with/', VersesEndsWith.as_view(), name='verses_ends_with_api'),
    path('api/mushaf-page/', MushafPageAPI.as_view(), name='mushaf_page_api'),

    # --> Mutashabihat API <--
    path('api/mutashabihat/by-ayah/', MutashabihatByAyah.as_view(), name='mutashabihat_by_ayah_api'),
    path('api/mutashabihat/search/', MutashabihatSearch.as_view(), name='mutashabihat_search_api'),
    path('api/mutashabihat/phrase/<int:phrase_id>/', MutashabihatPhraseDetail.as_view(), name='mutashabihat_phrase_detail_api'),
]

