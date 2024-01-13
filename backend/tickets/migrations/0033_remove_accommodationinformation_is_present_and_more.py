# Generated by Django 4.0.6 on 2022-08-28 14:14

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tickets", "0032_accommodationinformation_is_present_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="accommodationinformation",
            name="is_present",
        ),
        migrations.AddField(
            model_name="accommodationinformation",
            name="state",
            field=models.CharField(
                choices=[("N", "Not arrived"), ("A", "Arrived"), ("L", "Left")],
                default="N",
                max_length=1,
                verbose_name="State",
            ),
        ),
    ]