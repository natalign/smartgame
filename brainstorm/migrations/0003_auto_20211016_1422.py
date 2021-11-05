# Generated by Django 3.2.3 on 2021-10-16 14:22

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('brainstorm', '0002_auto_20211004_1602'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='id_site',
            field=models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Id для выгрузки на сайт'),
        ),
        migrations.AlterField(
            model_name='player',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
    ]
