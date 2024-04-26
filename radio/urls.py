from django.urls import path
from .views import RadiosList, RadioRankUp, RadioRankDown

app_name = 'radio'


urlpatterns = [
    path('', RadiosList.as_view(), name="radios_list"),
    path('rank/up/<int:id>/', RadioRankUp.as_view(), name="radio_rank_up"),
    path('rank/down/<int:id>/', RadioRankDown.as_view(), name="radio_rank_down"),
]
