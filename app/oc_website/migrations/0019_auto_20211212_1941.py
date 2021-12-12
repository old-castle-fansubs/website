# Generated by Django 3.2.6 on 2021-12-12 19:41
# pylint: disable=invalid-name

from django.db import migrations


def migrate_anidb_entries(apps, _schema_editor):
    AniDBEntry = apps.get_model("oc_website", "AniDBEntry")
    AnimeRequest = apps.get_model("oc_website", "AnimeRequest")
    for request in AnimeRequest.objects.all():
        anidb_entry, _created = AniDBEntry.objects.update_or_create(
            anidb_id=request.anidb_id,
            defaults={
                "image": request.anidb_image,
                "title": request.anidb_title,
                "type": request.anidb_type,
                "episodes": request.anidb_episodes,
                "synopsis": request.anidb_synopsis,
                "start_date": request.anidb_start_date,
                "end_date": request.anidb_end_date,
            },
        )
        request.anidb_entry = anidb_entry
        request.save()


class Migration(migrations.Migration):

    dependencies = [
        ("oc_website", "0018_anidbentry"),
    ]

    operations = [
        migrations.RunPython(migrate_anidb_entries, migrations.RunPython.noop),
    ]
