# Generated by Django 4.1.7 on 2024-03-22 22:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('radio', '0004_set_radios_rank_value'),
    ]

    operations = [
        migrations.AlterField(
            model_name='radio',
            name='rank',
            field=models.IntegerField(unique=True, verbose_name='Radio Rank'),
        ),
    ]
