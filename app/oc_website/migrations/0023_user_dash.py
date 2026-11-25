from django.db import migrations


def rename(old: str, new: str):
    def apply(apps, _schema_editor) -> None:
        apps.get_model("auth", "User").objects.filter(username=old).update(
            username=new
        )

    return apply


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("oc_website", "0022_news_author_dash"),
    ]

    operations = [
        migrations.RunPython(rename("rr-", "dash"), rename("dash", "rr-")),
    ]
