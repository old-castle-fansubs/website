from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("oc_website", "0011_projectrelease_scheduled_publication_date")
    ]

    operations = [
        migrations.AddField(
            model_name="animerequest",
            name="anidb_end_date",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="animerequest",
            name="anidb_episodes",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="animerequest",
            name="anidb_id",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="animerequest",
            name="anidb_image",
            field=models.FileField(
                blank=True, null=True, upload_to="requests/"
            ),
        ),
        migrations.AddField(
            model_name="animerequest",
            name="anidb_start_date",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="animerequest",
            name="anidb_synopsis",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="animerequest",
            name="anidb_title",
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name="animerequest",
            name="anidb_type",
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
    ]
