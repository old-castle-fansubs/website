from django.db import migrations

from oc_website.anidb import get_anidb_link_id


def add_anidb_id(apps, _schema_editor):
    AnimeRequest = apps.get_model(  # pylint: disable=invalid-name
        "oc_website", "AnimeRequest"
    )
    for anime_request in AnimeRequest.objects.all():
        anime_request.anidb_id = get_anidb_link_id(anime_request.anidb_url)
        anime_request.save()


def clear_anidb_id(apps, _schema_editor):
    AnimeRequest = apps.get_model(  # pylint: disable=invalid-name
        "oc_website", "AnimeRequest"
    )
    AnimeRequest.objects.all().update(anidb_id=None)


class Migration(migrations.Migration):
    dependencies = [
        ("oc_website", "0012_auto_20210828_1358"),
    ]

    operations = [
        migrations.RunPython(add_anidb_id, clear_anidb_id),
    ]
