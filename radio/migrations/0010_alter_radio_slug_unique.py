from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('radio', '0009_populate_radio_slugs'),
    ]

    operations = [
        migrations.AlterField(
            model_name='radio',
            name='slug',
            field=models.SlugField(allow_unicode=True, blank=True, max_length=150, unique=True, verbose_name='Slug'),
        ),
    ]
