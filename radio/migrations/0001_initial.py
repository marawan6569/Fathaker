# Generated by Django 4.1.7 on 2024-03-21 20:30

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Radio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Radio Name')),
                ('stream_url', models.URLField(verbose_name='Radio Stream URL')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Radio Description')),
                ('image', models.ImageField(blank=True, null=True, upload_to='radio/', verbose_name='Radio Image')),
            ],
        ),
    ]
