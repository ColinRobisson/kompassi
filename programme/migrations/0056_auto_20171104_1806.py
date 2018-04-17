# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-11-04 16:06
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('programme', '0055_programme_signup_link'),
    ]

    operations = [
        migrations.AddField(
            model_name='view',
            name='end_time',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='view',
            name='start_time',
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name='programmerole',
            name='person',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='programme_roles', to='core.Person'),
        ),
    ]