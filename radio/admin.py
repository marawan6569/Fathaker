from django.contrib import admin
from .models import Radio


# Register your models here.
@admin.register(Radio)
class RadioAdmin(admin.ModelAdmin):
    list_display = ['name', 'stream_link']
