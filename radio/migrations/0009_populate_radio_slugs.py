from django.db import migrations
from django.utils.text import slugify


def populate_slugs(apps, schema_editor):
    Radio = apps.get_model('radio', 'Radio')
    for radio in Radio.objects.all():
        if not radio.slug:
            base_slug = slugify(radio.name, allow_unicode=True)
            if not base_slug:
                base_slug = f"radio-{radio.pk}"
            slug = base_slug
            counter = 1
            while Radio.objects.filter(slug=slug).exclude(pk=radio.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            radio.slug = slug
            radio.save(update_fields=['slug'])


class Migration(migrations.Migration):

    dependencies = [
        ('radio', '0008_radio_likes_count_radio_slug_radio_views_count'),
    ]

    operations = [
        migrations.RunPython(populate_slugs, migrations.RunPython.noop),
    ]
