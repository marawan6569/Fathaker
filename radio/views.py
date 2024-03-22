from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404
from core.models import NavLink


# Create your views here.

class RadiosList(TemplateView):
    template_name = "radio/radios_list.html"
    
    def get_context_data(self, **kwargs):
        data = super().get_context_data()
        data['current_page_link'] = get_object_or_404(NavLink, name="radios_list")
        return data
