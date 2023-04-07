from django.contrib import admin
from django.db.models import Max
from django.utils.safestring import mark_safe
from django.urls import reverse
from .models import Radio, Category, RadioCategoriesM2M


# Register your models here.

@admin.register(RadioCategoriesM2M)
class RadioCategoriesM2MAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'category', 'rank', ]
    list_filter = ['category', ]


class RadioCategoriesM2MInline(admin.TabularInline):
    model = RadioCategoriesM2M


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'radios_count', 'rank', "category_rank_up_link", "category_rank_down_link", ]

    def category_rank_up_link(self, obj):
        if obj.rank == 1:
            return ""
        else:
            return mark_safe(
                f"""
                <a href="{reverse("radio:category_rank_up", args=[obj.id])}"> <img src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' 
                height='24' viewBox='0 0 24 24'%3E%3Cpath fill='currentColor' d='m13 5.586l-4.707 4.707a.999.999 0 1 0 
                1.414 1.414L12 9.414V17a1 1 0 1 0 2 0V9.414l2.293 2.293a.997.997 0 0 0 1.414 0a.999.999 0 0 0 0-1.414L13 
                5.586z'/%3E%3C/svg%3E%0A"/> </a>"""
            )

    def category_rank_down_link(self, obj):
        max_rank = Category.objects.aggregate(Max('rank'))
        if obj.rank == max_rank["rank__max"]:
            return ""
        else:
            return mark_safe(
                f"""
                <a href="{reverse("radio:category_rank_down", args=[obj.id])}"> <img src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' 
                height='24' viewBox='0 0 24 24'%3E%3Cpath fill='currentColor' d='M16.707 13.293a.999.999 0 0 0-1.414 0L13 
                15.586V8a1 1 0 1 0-2 0v7.586l-2.293-2.293a.999.999 0 1 0-1.414 1.414L12 19.414l4.707-4.707a.999.999 0 0 0 
                0-1.414z'/%3E%3C/svg%3E%0A"/> </a>"""
            )

    category_rank_up_link.short_description = "UP"
    category_rank_down_link.short_description = "DOWN"


@admin.register(Radio)
class RadioAdmin(admin.ModelAdmin):
    list_display = ['name', 'stream_link', 'categories_list', ]
    inlines = [RadioCategoriesM2MInline]
