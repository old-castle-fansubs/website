# Generated by Django 3.2.6 on 2021-08-18 22:22

from django.db import migrations

import oc_website.fields


class Migration(migrations.Migration):

    dependencies = [
        ("oc_website", "0003_auto_20210818_2152"),
    ]

    operations = [
        migrations.AlterField(
            model_name="projectreleaselink",
            name="url",
            field=oc_website.fields.MagnetURLField(max_length=1024),
        ),
    ]
