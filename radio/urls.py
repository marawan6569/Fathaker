from django.urls import path
from .views import RadiosList

app_name = 'radio'


urlpatterns = [
    path('', RadiosList.as_view(), name="radios_list"),
]
