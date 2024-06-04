from django.contrib import admin
from django.db.models import Max
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import Radio


# Register your models here.
@admin.register(Radio)
class RadioAdmin(admin.ModelAdmin):
    list_display = ['radio_image', 'name', 'audio', 'tag_list', 'radio_rank_up_link', 'radio_rank_down_link']

    list_filter = ['tags']

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('tags')

    def tag_list(self, obj):
        return u", ".join(o.name for o in obj.tags.all())

    tag_list.short_description = 'tags'

    def radio_rank_up_link(self, obj):
        if obj.rank == 1:
            return ""
        else:
            return mark_safe(
                f"""
                <a href="{reverse("radio:radio_rank_up", args=[obj.id])}"> <img title="{obj.rank}" src="data:image/svg+xml,
                %3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24'%3E%3Cpath 
                fill='currentColor' d='m13 5.586l-4.707 4.707a.999.999 0 1 0 1.414 1.414L12 9.414V17a1 1 0 1 0 2 
                0V9.414l2.293 2.293a.997.997 0 0 0 1.414 0a.999.999 0 0 0 0-1.414L13 5.586z'/%3E%3C/svg%3E%0A"/> </a>"""
            )

    def radio_rank_down_link(self, obj):
        max_rank = Radio.objects.all().aggregate(Max('rank'))
        if obj.rank == max_rank["rank__max"]:
            return ""
        else:
            return mark_safe(
                f"""
                <a href="{reverse("radio:radio_rank_down", args=[obj.id])}"> <img title="{obj.rank}" src="data:image/svg+xml,%3Csvg 
                xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24'%3E%3Cpath 
                fill='currentColor' d='M16.707 13.293a.999.999 0 0 0-1.414 0L13 15.586V8a1 1 0 1 0-2 
                0v7.586l-2.293-2.293a.999.999 0 1 0-1.414 1.414L12 19.414l4.707-4.707a.999.999 0 0 0 
                0-1.414z'/%3E%3C/svg%3E%0A"/> </a>"""
            )

    def radio_image(self, obj):
        img = obj.image.url if obj.image else "/static/radio/img/radio_img_not_available.png"
        return mark_safe(f"""
            <img src="{img}" style="width: 75px; height: 75px;"/>
        """)

    def audio(self, obj):
        return mark_safe(f"""
            <audio controls src="{obj.stream_url}">
        """)

    radio_rank_up_link.short_description = "UP"
    radio_rank_down_link.short_description = "DOWN"
    radio_image.short_description = "Image"
