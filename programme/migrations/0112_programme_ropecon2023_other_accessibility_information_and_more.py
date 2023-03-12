# Generated by Django 4.1.7 on 2023-03-11 17:13

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("programme", "0111_programme_ropecon2023_accessibility_cant_use_mic_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="programme",
            name="ropecon2023_other_accessibility_information",
            field=models.TextField(
                blank=True,
                default="",
                help_text="In the open field, define if necessary what features of your programme may possibly limit or enable participation (e.g. if the programme is available in sign language).",
                null=True,
                verbose_name="Other accessibility information",
            ),
        ),
        migrations.AlterField(
            model_name="programme",
            name="ropecon2023_language",
            field=models.CharField(
                choices=[
                    ("finnish", "Finnish"),
                    ("english", "English"),
                    ("language_free", "Language-free"),
                    ("finnish_or_english", "Finnish or English"),
                ],
                default="finnish",
                help_text="Finnish - choose this, if only Finnish is spoken in your programme.<br/>English - choose this, if only English is spoken in your programme.<br/>Language-free - choose this, if no Finnish or English is necessary to participate in the programme (e.g. a workshop with picture instructions or a dance where one can follow what others are doing).<br/>Finnish or English - choose this, if you are okay with having your programme language based on what language the attendees speak. Please write your title and programme description in both languages.",
                max_length=18,
                null=True,
                verbose_name="Choose the language used in your programme",
            ),
        ),
    ]
