from datetime import datetime, timezone

import pytest
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.test import Client

from oc_website.models import (
    AniDBEntry,
    AnimeRequest,
    Comment,
    FeaturedImage,
    Language,
    News,
    Project,
    ProjectExternalLink,
    ProjectRelease,
    ProjectReleaseFile,
    ProjectReleaseLink,
)

PAST = datetime(2021, 12, 1, tzinfo=timezone.utc)


@pytest.fixture(name="content")
def fixture_content() -> dict[str, int]:
    project = Project.objects.create(
        title="Glass Mask",
        slug="glass-mask",
        status="active",
        synopsis="An *actress*.",
        big_image="projects/big/glass-mask.jpg",
        small_image="projects/small/glass-mask.jpg",
    )
    ProjectExternalLink.objects.create(
        project=project, url="https://anidb.net/anime/1"
    )
    release = ProjectRelease.objects.create(
        project=project, release_date=PAST
    )
    ProjectReleaseLink.objects.create(
        release=release, url="magnet:?xt=urn:btih:" + "ab" * 20
    )
    release_file = ProjectReleaseFile.objects.create(
        release=release,
        file_name="glass-mask-01.mkv",
        file_version=1,
        episode_number=1,
        episode_title="The girl",
    )
    release_file.languages.add(Language.objects.create(name="eng"))
    news = News.objects.create(
        publication_date=PAST,
        title="Hello",
        author="dash",
        content="First **news**.",
    )
    FeaturedImage.objects.create(
        feature_date=PAST, image="featured_images/shot.jpg"
    )
    anidb_entry = AniDBEntry.objects.create(
        anidb_id=1, title="Glass Mask", episodes=23, start_date=PAST
    )
    anime_request = AnimeRequest.objects.create(
        request_date=PAST, anidb_entry=anidb_entry
    )
    Comment.objects.create(
        comment_date=PAST, text="Guest book *comment*", author="someone"
    )
    Comment.objects.create(
        content_type=ContentType.objects.get_for_model(AnimeRequest),
        object_id=anime_request.pk,
        comment_date=PAST,
        text="Please!",
        author="someone",
    )
    return {"news": news.pk, "anime_request": anime_request.pk}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url",
    [
        "/",
        "/news/",
        "/news/{news}/",
        "/about/",
        "/projects/",
        "/project/glass-mask/",
        "/featured_images/",
        "/admin/login/",
    ],
)
def test_page_renders(content: dict[str, int], client: Client, url: str) -> None:
    response = client.get(url.format(**content))
    assert response.status_code == 200


STAFF_URLS = [
    "/anime_requests/",
    "/anime_requests/?search_text=glass&sort=title",
    "/anime_request/{anime_request}/",
    "/guest_book/",
]


@pytest.fixture(name="staff_client")
def fixture_staff_client(client: Client) -> Client:
    client.force_login(
        User.objects.create(
            username="admin", is_staff=True, is_superuser=True
        )
    )
    return client


@pytest.mark.django_db
@pytest.mark.parametrize("url", STAFF_URLS)
def test_staff_page_renders_for_staff(
    content: dict[str, int], staff_client: Client, url: str
) -> None:
    response = staff_client.get(url.format(**content))
    assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize("url", STAFF_URLS)
def test_staff_page_is_hidden_from_others(
    content: dict[str, int], client: Client, url: str
) -> None:
    response = client.get(url.format(**content))
    assert response.status_code == 404


@pytest.mark.django_db
def test_staff_tabs(staff_client: Client) -> None:
    assert b"Guest book" not in Client().get("/").content
    assert b"Guest book" in staff_client.get("/").content


@pytest.mark.django_db
@pytest.mark.parametrize(
    "model",
    [
        "anidbentry",
        "animerequest",
        "comment",
        "featuredimage",
        "language",
        "news",
        "project",
        "projectrelease",
    ],
)
def test_admin_list_renders(
    content: dict[str, int],  # pylint: disable=unused-argument
    staff_client: Client,
    model: str,
) -> None:
    response = staff_client.get(f"/admin/oc_website/{model}/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_home_without_featured_image(client: Client) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert b"id='featured'" not in response.content
