from django.urls import path
from .views import RadiosList, category_rank_up, category_rank_down

app_name = 'radio'


urlpatterns = [
    path('', RadiosList.as_view(), name="radios_list"),
    path('category_rank_up/<int:category_id>', category_rank_up, name="category_rank_up"),
    path('category_rank_down/<int:category_id>', category_rank_down, name="category_rank_down"),
]
