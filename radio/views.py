from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Max

from core.models import NavLink
from .models import Category, RadioCategoriesM2M


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
                "radios": category.radios.order_by('radiocategoriesm2m__rank')
            }
            for category in Category.objects.prefetch_related().all()
        ]
        return data


@staff_member_required
def category_rank_up(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if category.rank > 1:
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

    if category.rank < max_rank["rank__max"]:
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


@staff_member_required
def radio_rank_in_category_up(request, rel_id):
    rel = get_object_or_404(RadioCategoriesM2M, id=rel_id)
    if rel.rank > 1:
        upper_rel = get_object_or_404(RadioCategoriesM2M, category=rel.category, rank=rel.rank - 1)

        # set current radio rank to unused value
        rel.rank = -1
        rel.save()

        # set upper radio rank to current radio rank
        upper_rel.rank = upper_rel.rank + 1
        upper_rel.save()

        # set current radio rank to upper radio rank
        rel.rank = upper_rel.rank - 1
        rel.save()

        messages.add_message(
            request, messages.SUCCESS,
            f"Radio {rel.radio.name} rank updated in Category {rel.category.name} "
            f"from {upper_rel.rank} to {rel.rank} successfully"
        )

    return redirect(request.META.get('HTTP_REFERER') if request.META.get('HTTP_REFERER') else "/admin/radio"
                                                                                              "/radiocategoriesm2m/")


@staff_member_required
def radio_rank_in_category_down(request, rel_id):
    rel = get_object_or_404(RadioCategoriesM2M, id=rel_id)
    max_rank = RadioCategoriesM2M.objects.filter(category=rel.category).aggregate(Max('rank'))

    if rel.rank < max_rank["rank__max"]:
        lower_rel = get_object_or_404(RadioCategoriesM2M, category=rel.category, rank=rel.rank + 1)

        # set current radio rank to unused value
        rel.rank = -1
        rel.save()

        # set lower radio rank to radio category rank
        lower_rel.rank = lower_rel.rank - 1
        lower_rel.save()

        # set current radio rank to lower radio rank
        rel.rank = lower_rel.rank + 1
        rel.save()

        messages.add_message(
            request, messages.SUCCESS,
            f"Radio {rel.radio.name} rank updated in Category {rel.category.name} "
            f"from {lower_rel.rank} to {rel.rank} successfully"
        )

    return redirect(request.META.get('HTTP_REFERER') if request.META.get('HTTP_REFERER') else "/admin/radio"
                                                                                              "/radiocategoriesm2m/")
