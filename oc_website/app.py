import re
from datetime import datetime, timezone
from functools import cache
from typing import Any, Callable, Optional

import werkzeug.routing
from flask import Flask, Response, redirect, render_template, request

from oc_website.lib.comments import Comment, get_comments, save_comments
from oc_website.lib.common import first
from oc_website.lib.featured_images import get_featured_images
from oc_website.lib.jinja_env import setup_jinja_env
from oc_website.lib.news import get_news
from oc_website.lib.projects import get_projects
from oc_website.lib.releases import get_releases
from oc_website.lib.requests import Request as SubRequest
from oc_website.lib.requests import (
    get_requests,
    is_same_anidb_link,
    is_valid_anidb_link,
)
from oc_website.lib.requests import save_requests as save_sub_requests
from oc_website.lib.thumbnails import generate_thumbnail

app = Flask(__name__)
setup_jinja_env(app.jinja_env)

GUEST_BOOK_THREAD_ID = 10


def init() -> None:
    for featured_image in get_featured_images():
        generate_thumbnail(
            featured_image.absolute_path,
            featured_image.absolute_thumbnail_path,
        )

    class RegexConverter(werkzeug.routing.BaseConverter):
        def __init__(self, url_map: Any, *items: Any) -> None:
            super().__init__(url_map)
            self.regex = items[0]

    app.url_map.converters["regex"] = RegexConverter
    app.config["TEMPLATES_AUTO_RELOAD"] = True


init()


@app.after_request
def cors(response: Response) -> Response:
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


def custom_cache(func: Callable[..., Any]) -> Callable[..., Any]:
    if not app.debug:
        return cache(func)
    setattr(func, "cache_clear", lambda: None)
    return func


@app.route("/index.html")
@app.route("/")
@custom_cache
def home() -> Response:
    return render_template("home.html", featured_images=get_featured_images())


@app.route("/news.html")
@custom_cache
def news() -> Response:
    news_items = list(get_news())
    news_items.sort(key=lambda news_item: news_item.stem, reverse=True)
    return render_template("news_list.html", news_entries=news_items)


@app.route("/projects.html")
@custom_cache
def projects() -> Response:
    project_items = list(get_projects(get_releases()))
    project_items.sort(key=lambda project_item: project_item.title)
    return render_template("projects.html", projects=project_items)


@app.route("/project-<string:project_name>.html")
@custom_cache
def project(project_name: str) -> Response:
    for project_item in get_projects(get_releases()):
        if project_name == project_item.stem:
            return render_template(
                "projects/" + project_item.stem + ".html", project=project_item
            )
    return projects()


@app.route("/about.html")
@custom_cache
def about() -> Response:
    return render_template("about.html")


@app.route("/featured.html")
@custom_cache
def featured_images() -> Response:
    return render_template(
        "featured.html", featured_images=get_featured_images()
    )


@app.route("/requests.html")
@custom_cache
def requests() -> Response:
    request_items = list(get_requests())
    request_items.sort(key=lambda sub_request: sub_request.title.lower())
    return render_template("request_list.html", requests=request_items)


@app.route("/request_add.html", methods=["GET", "POST"])
def request_add() -> Response:
    title = request.form.get("title", "").strip()
    anidb_link = request.form.get("anidb_link", "").strip()
    comment = request.form.get("comment", "").strip()

    sub_requests = get_requests()
    remote_addr: Optional[str]
    if request.headers.getlist("X-Forwarded-For"):
        remote_addr = request.headers.getlist("X-Forwarded-For")[0]
    else:
        remote_addr = request.remote_addr

    sub_request = SubRequest(
        title=title,
        date=datetime.now(timezone.utc).astimezone(),
        anidb_link=anidb_link,
        comment=comment,
        remote_addr=remote_addr,
    )

    errors: list[str] = []

    if request.method == "POST":
        if request.form.get("phone") or request.form.get("message"):
            errors.append("Human verification failed.")
        if not sub_request.title:
            errors.append("Request title cannot be empty.")
        if not sub_request.anidb_link:
            errors.append("AniDB link cannot be empty.")
        elif not is_valid_anidb_link(sub_request.anidb_link):
            errors.append("The provided AniDB link appears to be invalid.")

        if any(
            is_same_anidb_link(sub_request.anidb_link, r.anidb_link)
            for r in sub_requests
        ):
            errors.append(
                "Anime with this AniDB link had been already requested."
            )

        if not errors:
            sub_requests.append(sub_request)
            save_sub_requests(sub_requests)
            requests.cache_clear()
            return redirect("requests.html", code=302)

    return render_template(
        "request_add.html", request=sub_request, errors=errors
    )


@app.route("/guest_book.html")
@custom_cache
def guest_book() -> Response:
    return render_template(
        "guest_book.html",
        thread_id=GUEST_BOOK_THREAD_ID,
        comments=[
            comment
            for comment in get_comments()
            if comment.thread_id == GUEST_BOOK_THREAD_ID
        ],
    )


@app.route("/comment_add.html", methods=["GET", "POST"])
def comment_add() -> Response:
    parent_comment_id: int
    try:
        parent_comment_id = int(request.args.get("pid", ""))
    except (TypeError, ValueError):
        parent_comment_id = 0

    try:
        thread_id = int(request.args.get("tid", ""))
    except (TypeError, ValueError):
        thread_id = 0

    is_preview = request.form.get("submit") == "preview"
    text = request.form.get("text", "").strip()
    author = request.form.get("author", "").strip()
    website = request.form.get("website", "").strip()
    email = request.form.get("email", "").strip()

    comments = get_comments()
    parent_comment: Optional[Comment] = first(
        c for c in comments if c.comment_id == parent_comment_id
    )
    if parent_comment:
        thread_id = parent_comment.thread_id

    form_url = f"comment_add.html?tid={thread_id}&pid={parent_comment_id}"

    remote_addr: Optional[str]
    if request.headers.getlist("X-Forwarded-For"):
        remote_addr = request.headers.getlist("X-Forwarded-For")[0]
    else:
        remote_addr = request.remote_addr

    comment_id = (
        max(comment.comment_id for comment in comments) + 1 if comments else 0
    )

    comment = Comment(
        thread_id=thread_id,
        comment_id=comment_id,
        parent_comment_id=parent_comment_id or None,
        created=datetime.now(timezone.utc).astimezone(),
        remote_addr=remote_addr,
        text=text,
        author=author,
        email=email,
        website=website,
        likes=0,
    )

    errors: list[str] = []

    if request.method == "POST":
        if request.form.get("phone") or request.form.get("message"):
            errors.append("Human verification failed.")
        if not comment.text:
            errors.append("Comment content cannot be empty.")
        if not comment.author:
            errors.append("Comment author cannot be empty.")
        if not comment.thread_id:
            errors.append("Comment thread ID cannot be empty.")
        if not re.search("[a-zA-Z']{3,}", comment.text):
            errors.append(
                "Add a few more letters to make your comment more interesting."
            )
        if (
            comments
            and comments[0].text == comment.text
            and comments[0].author == comment.author
        ):
            errors.append("A comment with this exact content already exists.")

        if not errors and not is_preview:
            comments.insert(0, comment)
            save_comments(comments)
            guest_book.cache_clear()
            return redirect("guest_book.html", code=302)

    return render_template(
        "comment_add.html",
        form_url=form_url,
        parent_comment=parent_comment,
        comment=comment,
        preview=is_preview,
        errors=errors,
    )


@app.errorhandler(404)
def page_not_found(_e: Exception) -> Response:
    return render_template("404.html"), 404
