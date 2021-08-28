from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("oc_website", "0013_auto_20210828_1406"),
    ]

    operations = [
        migrations.RemoveField(model_name="animerequest", name="anidb_url"),
        migrations.AlterField(
            model_name="animerequest",
            name="anidb_id",
            field=models.IntegerField(),
        ),
    ]
