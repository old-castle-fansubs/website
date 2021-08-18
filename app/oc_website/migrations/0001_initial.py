import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies: list[tuple[str, str]] = []

    operations = [
        migrations.CreateModel(
            name="Language",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=10)),
            ],
        ),
        migrations.CreateModel(
            name="Project",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=200)),
                ("slug", models.CharField(max_length=30)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("ACTIVE", "active"),
                            ("FINISHED", "finished"),
                        ],
                        max_length=30,
                    ),
                ),
                (
                    "takedown_request",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                ("is_visible", models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name="ProjectRelease",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("release_date", models.DateTimeField()),
                ("is_visible", models.BooleanField(default=True)),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="releases",
                        to="oc_website.project",
                    ),
                ),
            ],
            options={
                "unique_together": {("project_id", "release_date")},
            },
        ),
        migrations.CreateModel(
            name="ProjectReleaseLink",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("url", models.URLField()),
                (
                    "release",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="links",
                        to="oc_website.projectrelease",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ProjectReleaseFile",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("file_name", models.CharField(max_length=256)),
                ("file_version", models.IntegerField()),
                ("episode_number", models.IntegerField(blank=True, null=True)),
                (
                    "episode_title",
                    models.CharField(blank=True, max_length=200, null=True),
                ),
                (
                    "languages",
                    models.ManyToManyField(to="oc_website.Language"),
                ),
                (
                    "release",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="files",
                        to="oc_website.projectrelease",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ProjectExternalLink",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("url", models.URLField()),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="links",
                        to="oc_website.project",
                    ),
                ),
            ],
        ),
    ]
