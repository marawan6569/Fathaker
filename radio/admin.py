from django.contrib import admin
from .models import Radio, Category

# Register your models here.


@admin.register(Category)
class RadioAdmin(admin.ModelAdmin):
    list_display = ['name', 'radios_count', ]


@admin.register(Radio)
class RadioAdmin(admin.ModelAdmin):
    list_display = ['name', 'stream_link', 'categories_list', ]
