# Generated by Django 3.2.6 on 2021-08-22 16:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("oc_website", "0010_projectrelease_filename"),
    ]

    operations = [
        migrations.AddField(
            model_name="projectrelease",
            name="scheduled_publication_date",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
