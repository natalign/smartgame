# Generated by Django 3.2.3 on 2021-10-18 15:55

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('brainstorm', '0004_auto_20211017_1329'),
    ]

    operations = [
        migrations.AlterField(
            model_name='player',
            name='name',
            field=models.CharField(blank=True, max_length=200, validators=[django.core.validators.MinLengthValidator(2, 'Имя должно быть длиннее чем 1 символ')], verbose_name='ФИО'),
        ),
    ]
