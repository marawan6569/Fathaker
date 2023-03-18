from django.views.generic import TemplateView

# Create your views here.


class HomePage(TemplateView):
    template_name = 'core/home_page.html'
