from django.contrib import admin
from .models import Radio


# Register your models here.
@admin.register(Radio)
class RadioAdmin(admin.ModelAdmin):
    list_display = ['name', 'stream_link', 'rank', 'tag_list']

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('tags')

    def tag_list(self, obj):
        return u", ".join(o.name for o in obj.tags.all())

    tag_list.short_description = 'tags'
