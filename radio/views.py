from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Max

from core.models import NavLink
from .models import Radio, Category


# Create your views here.

class RadiosList(TemplateView):
    template_name = "radio/radios_list.html"
    
    def get_context_data(self, **kwargs):
        data = super().get_context_data()
        data['current_page_link'] = get_object_or_404(NavLink, name="radios_list")
        data['categories'] = [
            {
                "category_name": category.name,
                "radios_count": category.radios_count(),
                "radios": category.radios
            }
            for category in Category.objects.prefetch_related().all()
        ]
        return data


# @staff_member_required
def category_rank_up(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if category.rank >= 1:
        upper_category = get_object_or_404(Category, rank=category.rank - 1)

        # set current category rank to unused value
        category.rank = -1
        category.save()

        # set upper category rank to current category rank
        upper_category.rank = upper_category.rank + 1
        upper_category.save()

        # set current category rank to upper category rank
        category.rank = upper_category.rank - 1
        category.save()

        messages.add_message(
            request, messages.SUCCESS,
            f"Category {category.name} rank updated from {upper_category.rank} to {category.rank} successfully"
        )

    return redirect(request.META.get('HTTP_REFERER') if request.META.get('HTTP_REFERER') else "/admin/radio/category/")


@staff_member_required
def category_rank_down(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    max_rank = Category.objects.aggregate(Max('rank'))

    if category.rank <= max_rank["rank__max"]:
        lower_category = get_object_or_404(Category, rank=category.rank + 1)

        # set current category rank to unused value
        category.rank = -1
        category.save()

        # set lower category rank to current category rank
        lower_category.rank = lower_category.rank - 1
        lower_category.save()

        # set current category rank to lower category rank
        category.rank = lower_category.rank + 1
        category.save()

        messages.add_message(
            request, messages.SUCCESS,
            f"Category {category.name} rank updated from {lower_category.rank} to {category.rank} successfully"
        )

    return redirect(request.META.get('HTTP_REFERER') if request.META.get('HTTP_REFERER') else "/admin/radio/category/")



