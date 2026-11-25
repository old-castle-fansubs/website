from django.db import migrations


def rename(old: str, new: str):
    def apply(apps, _schema_editor) -> None:
        apps.get_model("oc_website", "News").objects.filter(
            author=old
        ).update(author=new)

    return apply


class Migration(migrations.Migration):
    dependencies = [
        ("oc_website", "0021_auto_20211223_1706"),
    ]

    operations = [
        migrations.RunPython(rename("rr-", "dash"), rename("dash", "rr-")),
    ]
