from django.contrib import admin
from .models import Radio, Category

# Register your models here.


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'rank', 'radios_count', ]
    list_editable = ['rank']
    ordering = ['rank']


@admin.register(Radio)
class RadioAdmin(admin.ModelAdmin):
    list_display = ['name', 'stream_link', 'categories_list', ]
