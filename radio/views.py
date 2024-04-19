from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from core.models import NavLink
from .models import Radio


# Create your views here.


class RadioRankDown(APIView):
    allowed_methods = ['get']

    def get(self, request, *args, **kwargs):
        try:
            radio_id = self.kwargs.get("id", None)
            radio = Radio.objects.get(id=radio_id)
            prev_radio = Radio.objects.get(rank=radio.rank + 1)

            current_rank = radio.rank
            prev_rank = prev_radio.rank

            radio.rank = - 1
            prev_radio.rank = -2
            radio.save()
            prev_radio.save()

            radio.rank = prev_rank
            prev_radio.rank = current_rank
            radio.save()
            prev_radio.save()

            messages.success(request, f'{radio.name} rank changed from {current_rank} to {prev_rank} successfully.')
        except Exception as e:
            messages.error(request, f'Failed to swap ranks.\n Errors: {e}')

        # return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('default-url')))
        return redirect(reverse("admin:radio_radio_changelist"))


class RadioRankUp(APIView):
    allowed_methods = ['get']

    def get(self, request, *args, **kwargs):
        try:
            radio_id = self.kwargs.get("id", None)
            radio = Radio.objects.get(id=radio_id)
            next_radio = Radio.objects.get(rank=radio.rank - 1)

            current_rank = radio.rank
            next_rank = next_radio.rank

            radio.rank = - 1
            next_radio.rank = -2
            radio.save()
            next_radio.save()

            radio.rank = next_rank
            next_radio.rank = current_rank
            radio.save()
            next_radio.save()

            messages.success(request, f'{radio.name} rank changed from {current_rank} to {next_rank} successfully.')
        except Exception as e:
            messages.error(request, f'Failed to swap ranks.\n Errors: {e}')

        # return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('default-url')))
        return redirect(reverse("admin:radio_radio_changelist"))


class RadiosList(TemplateView):
    template_name = "radio/radios_list.html"

    def get_context_data(self, **kwargs):
        data = super().get_context_data()
        data['radios'] = Radio.objects.all().prefetch_related("tags")
        data['current_page_link'] = get_object_or_404(NavLink, name="radios_list")
        return data
