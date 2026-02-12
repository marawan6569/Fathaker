from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404
from core.models import NavLink
from .models import Surah


class QuranSearch(TemplateView):
    template_name = "verses/quran_search.html"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['surahs'] = Surah.objects.all()
        try:
            data['current_page_link'] = NavLink.objects.get(name="quran_search")
        except NavLink.DoesNotExist:
            pass
        return data


class QuranMushaf(TemplateView):
    template_name = "verses/quran_mushaf.html"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['surahs'] = Surah.objects.all()
        try:
            data['current_page_link'] = NavLink.objects.get(name="quran_mushaf")
        except NavLink.DoesNotExist:
            pass
        return data

