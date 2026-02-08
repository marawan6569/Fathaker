from django.urls import path, register_converter
from .views import RadiosList, RadioRankUp, RadioRankDown, RadioDetail, RadioLike

app_name = 'radio'


class UnicodeSlugConverter:
    regex = '[-\\w]+'

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value


register_converter(UnicodeSlugConverter, 'uslug')

urlpatterns = [
    path('', RadiosList.as_view(), name="radios_list"),
    path('rank/up/<int:id>/', RadioRankUp.as_view(), name="radio_rank_up"),
    path('rank/down/<int:id>/', RadioRankDown.as_view(), name="radio_rank_down"),
    path('api/<uslug:slug>/like/', RadioLike.as_view(), name="radio_like"),
    path('<uslug:slug>/', RadioDetail.as_view(), name="radio_detail"),
]
