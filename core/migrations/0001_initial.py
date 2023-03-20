# Generated by Django 4.1.7 on 2023-03-18 22:59

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='NavLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='Link Name (In Database)')),
                ('display_name', models.CharField(max_length=100, verbose_name='Link Name')),
                ('path', models.CharField(max_length=100, verbose_name='Link path')),
                ('icon', models.CharField(max_length=100, verbose_name='FontAwesome Icon Class')),
                ('link_type', models.CharField(choices=[(0, 'Navbar'), (1, 'Footer Links'), (2, 'Footer Social')], max_length=2, verbose_name='Link Type')),
                ('is_active', models.BooleanField(default=True, verbose_name='Is Link Active ? ')),
            ],
        ),
    ]