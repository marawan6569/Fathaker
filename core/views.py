from django.views.generic import RedirectView

# Create your views here.


class HomePage(RedirectView):
    pattern_name = 'radio:radios_list'

