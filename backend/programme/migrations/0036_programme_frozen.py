# Generated by Django 1.9.5 on 2016-06-27 17:49


from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("programme", "0035_auto_20160623_0037"),
    ]

    operations = [
        migrations.AddField(
            model_name="programme",
            name="frozen",
            field=models.BooleanField(
                default=False,
                help_text="When a programme is frozen, its details can no longer be edited by the programme host. The programme manager may continue to edit these, however.",
                verbose_name="Frozen",
            ),
        ),
    ]