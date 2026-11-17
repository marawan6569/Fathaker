from django import template
from radio.images import image_url

register = template.Library()


@register.filter
def radio_image(image, variant):
    return image_url(image, variant)
