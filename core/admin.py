from django.contrib import admin
from .models import NavLink

admin.site.site_header = "Fathaker administration"
admin.site.site_title = "Fathaker administration"
admin.site.index_title = "Fathaker administration"


# Register your models here.


@admin.register(NavLink)
class NavLinkAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'destination', 'link_type', 'is_active', 'is_external', ]
    list_filter = ['link_type', 'is_active', 'is_external', ]
