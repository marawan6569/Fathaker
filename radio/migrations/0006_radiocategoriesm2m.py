# Generated by Django 4.1.7 on 2023-04-07 00:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('radio', '0005_alter_category_options'),
    ]

    operations = [
        migrations.CreateModel(
            name='RadioCategoriesM2M',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rank', models.IntegerField(db_index=True, verbose_name='Radio Rank in Category')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='radio.category', verbose_name='Category')),
                ('radio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='radio.radio', verbose_name='Radio')),
            ],
            options={
                'unique_together': {('category', 'rank'), ('radio', 'category')},
                'ordering': ['category', 'rank']
            },
        ),
    ]
