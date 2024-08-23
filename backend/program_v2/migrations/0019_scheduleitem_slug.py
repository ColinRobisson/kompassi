# Generated by Django 5.0.8 on 2024-08-18 08:31

import django.core.validators
from django.db import migrations, models

from core.utils.model_utils import slugify


def populate_slug(apps, schema_editor):
    ScheduleItem = apps.get_model("program_v2", "ScheduleItem")
    for schedule_item in ScheduleItem.objects.all():
        schedule_item.slug = f"{schedule_item.program.slug}-{slugify(schedule_item.subtitle)}"
        schedule_item.save(update_fields=["slug"])


class Migration(migrations.Migration):
    dependencies = [
        ("program_v2", "0018_rename_other_fields_program_annotations"),
    ]

    operations = [
        migrations.AddField(
            model_name="scheduleitem",
            name="slug",
            field=models.CharField(
                default="",
                help_text='Tekninen nimi eli "slug" näkyy URL-osoitteissa. Sallittuja merkkejä ovat pienet kirjaimet, numerot ja väliviiva. Teknistä nimeä ei voi muuttaa luomisen jälkeen.',
                max_length=255,
                validators=[
                    django.core.validators.RegexValidator(
                        message="Tekninen nimi saa sisältää vain pieniä kirjaimia, numeroita sekä väliviivoja.",
                        regex="[a-z0-9-]+",
                    )
                ],
                verbose_name="Tekninen nimi",
            ),
            preserve_default=False,
        ),
        migrations.RunPython(populate_slug),
    ]