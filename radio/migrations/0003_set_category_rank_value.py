# Generated by Django 4.1.7 on 2023-03-31 15:01

from django.db import migrations


def ranking_categories(apps, schema_editor):
    """
    Set Category Value Rank To  Category Id as initial value
    """
    Category = apps.get_model('radio', 'Category')
    for category in Category.objects.all():
        category.rank = category.id
        category.save()


class Migration(migrations.Migration):

    dependencies = [
        ('radio', '0002_category_rank_alter_category_name'),
    ]

    operations = [
        migrations.RunPython(ranking_categories),
    ]
