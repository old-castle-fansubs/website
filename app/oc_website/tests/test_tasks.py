from collections.abc import Iterable
from pathlib import Path
from unittest.mock import patch

import pytest
from django.conf import settings
from django.test import override_settings

from oc_website.tasks.releases import BasePublisher, publish_release
from oc_website.tests.factories import ProjectReleaseFactory


@pytest.fixture(name="override_dirs")
def fixture_override_dirs(tmp_path: Path) -> Iterable[None]:
    with override_settings(
        DATA_DIR=tmp_path / "data",
        TORRENTS_DIR=tmp_path / "torrents",
        TRANSMISSION_WATCHDIR=tmp_path / "transmission-watchdir",
        IRCBOT_WATCHDIR=tmp_path / "ircbot-watchdir",
    ):
        settings.DATA_DIR.mkdir()
        settings.TORRENTS_DIR.mkdir()
        settings.TRANSMISSION_WATCHDIR.mkdir()
        yield


def test_publishers_have_unique_names() -> None:
    publisher_cls_names = [
        publisher_cls.name for publisher_cls in BasePublisher.__subclasses__()
    ]
    assert len(publisher_cls_names) == len(set(publisher_cls_names))


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
@pytest.mark.django_db
def test_publish_release(
    override_dirs: None,  # pylint: disable=unused-argument
    project_release_factory: ProjectReleaseFactory,
) -> None:
    data_path = settings.DATA_DIR / "test file.txt"
    data_path.write_text("123")
    project_release = project_release_factory(filename="test file.txt")

    with patch(
        "oc_website.tasks.releases.AnidexPublisher.publish",
        return_value="anidex_url",
    ) as fake_anidex_publish, patch(
        "oc_website.tasks.releases.NyaaSiPublisher.publish",
        return_value="nyaa_si_url",
    ) as fake_nyaa_si_publish:
        publish_release.s(project_release.pk, dry_run=False).apply()

    project_release.refresh_from_db()

    assert project_release.scheduled_publication_date is None
    assert project_release.is_visible is True
    assert project_release.links.count() == 3
    assert sorted(project_release.links.values_list("url", flat=True)) == [
        "anidex_url",
        (
            "magnet:?xt=urn:btih:ca5b7bcf892317da519b88162ad81405f21de8c7"
            "&dn=test+file.txt&xl=3"
            "&tr=http%3A%2F%2Fanidex.moe%3A6969%2Fannounce"
            "&tr=http%3A%2F%2Fnyaa.tracker.wf%3A7777%2Fannounce"
            "&tr=udp%3A%2F%2Ftracker.uw0.xyz%3A6969"
        ),
        "nyaa_si_url",
    ]

    torrent_path = settings.TORRENTS_DIR / "test file.torrent"
    torrent_path_for_transmission = (
        settings.TRANSMISSION_WATCHDIR / "test file.torrent"
    )
    assert torrent_path.exists()
    assert torrent_path_for_transmission.exists()

    assert (settings.IRCBOT_WATCHDIR / "test file.txt").is_symlink()
    assert (settings.IRCBOT_WATCHDIR / "test file.txt").read_text() == "123"

    fake_anidex_publish.assert_called_once_with(
        torrent_path, data_path, dry_run=False
    )
    fake_nyaa_si_publish.assert_called_once_with(
        torrent_path, data_path, dry_run=False
    )
