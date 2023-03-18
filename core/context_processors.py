from .models import NavLink


def get_nav_links(request):
    return {
        "navbar_links": NavLink.objects.filter(link_type="0"),
        "footer_links": NavLink.objects.filter(link_type="1"),
        "footer_social": NavLink.objects.filter(link_type="2"),
    }
