from django.urls import path
from .views import RadiosList, category_rank_up, category_rank_down, radio_rank_in_category_up, radio_rank_in_category_down

app_name = 'radio'


urlpatterns = [
    path('', RadiosList.as_view(), name="radios_list"),
    path('category_rank_up/<int:category_id>', category_rank_up, name="category_rank_up"),
    path('category_rank_down/<int:category_id>', category_rank_down, name="category_rank_down"),
    path('radio_rank_in_category_up/<int:rel_id>', radio_rank_in_category_up, name="radio_rank_in_category_up"),
    path('radio_rank_in_category_down/<int:rel_id>', radio_rank_in_category_down, name="radio_rank_in_category_down"),
]
