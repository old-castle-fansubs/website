# Generated by Django 3.2.6 on 2021-08-21 14:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("oc_website", "0009_auto_20210819_2136"),
    ]

    operations = [
        migrations.AddField(
            model_name="projectrelease",
            name="filename",
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
    ]
