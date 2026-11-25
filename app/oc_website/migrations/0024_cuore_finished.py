from django.db import migrations


def set_status(status: str):
    def apply(apps, _schema_editor) -> None:
        apps.get_model("oc_website", "Project").objects.filter(
            slug="cuore"
        ).update(status=status)

    return apply


class Migration(migrations.Migration):
    dependencies = [
        ("oc_website", "0023_user_dash"),
    ]

    operations = [
        migrations.RunPython(set_status("finished"), set_status("active")),
    ]
