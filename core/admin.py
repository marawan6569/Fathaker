from django.contrib import admin
from .models import NavLink

# Register your models here.


@admin.register(NavLink)
class NavLinkAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'path', 'link_type', 'is_active',]
    list_filter = ['link_type', 'is_active']
