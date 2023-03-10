from django.urls import path
from .api_views import VersesList

app_name = 'verses'


urlpatterns = [



    # --> API <--
    path('api/verses_list', VersesList.as_view(), name='verses_list_api'),
]
