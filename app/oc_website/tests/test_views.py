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
        project=project, release_date=PAST, filename="glass-mask-01.mkv"
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
        author="rr-",
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
        "/anime_requests/",
        "/anime_requests/?search_text=glass&sort=title",
        "/anime_request/{anime_request}/",
        "/anime_request/{anime_request}/comment/",
        "/anime_request/add/",
        "/guest_book/",
        "/guest_book/comment/",
        "/featured_images/",
        "/admin/login/",
    ],
)
def test_page_renders(content: dict[str, int], client: Client, url: str) -> None:
    response = client.get(url.format(**content))
    assert response.status_code == 200


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
    client: Client,
    model: str,
) -> None:
    client.force_login(
        User.objects.create_superuser("admin", "admin@example.com", "admin")
    )
    response = client.get(f"/admin/oc_website/{model}/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_home_without_featured_image(client: Client) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert b"id='featured'" not in response.content
