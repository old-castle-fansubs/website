import typing as T
from datetime import datetime

import werkzeug.routing
from flask import (
    Flask,
    Response,
    redirect,
    render_template,
    request,
    send_from_directory,
)

from oc_website.lib.comments import Comment, get_comments, save_comments
from oc_website.lib.common import STATIC_DIR, first
from oc_website.lib.featured_images import get_featured_images
from oc_website.lib.jinja_env import setup_jinja_env
from oc_website.lib.news import get_news
from oc_website.lib.projects import get_projects
from oc_website.lib.releases import get_releases
from oc_website.lib.requests import Request as SubRequest
from oc_website.lib.requests import get_requests as get_sub_requests
from oc_website.lib.requests import is_same_anidb_link, is_valid_anidb_link
from oc_website.lib.requests import save_requests as save_sub_requests
from oc_website.lib.thumbnails import generate_thumbnail

app = Flask(__name__)
setup_jinja_env(app.jinja_env)

FEATURED_IMAGES = list(get_featured_images())
RELEASES = list(get_releases())
PROJECTS = list(
    sorted(get_projects(RELEASES), key=lambda project: project.title)
)
NEWS = sorted(get_news(), key=lambda news: news.stem, reverse=True)

GUEST_BOOK_CACHE = ""
GUEST_BOOK_TID = 10


def init() -> None:
    for featured_image in FEATURED_IMAGES:
        generate_thumbnail(featured_image.path, featured_image.thumbnail_path)

    class RegexConverter(werkzeug.routing.BaseConverter):
        def __init__(self, url_map: T.Any, *items: T.Any) -> None:
            super(RegexConverter, self).__init__(url_map)
            self.regex = items[0]

    app.url_map.converters["regex"] = RegexConverter


init()


@app.route(
    '/<regex(".*\\.(cs|j)s|data/.*|img(-thumb)?/.*|favicon\\.ico|robots\\.txt"):path>'
)
def app_static(path: str) -> T.Any:
    return send_from_directory(STATIC_DIR, path)


@app.after_request
def cors(response: Response) -> Response:
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


@app.route("/")
@app.route("/index.html")
def app_home() -> str:
    return render_template("home.html", featured_images=FEATURED_IMAGES)


@app.route("/news.html")
def app_news() -> str:
    return render_template("news_list.html", news_entries=NEWS)


@app.route("/projects.html")
def app_projects() -> str:
    return render_template("projects.html", projects=PROJECTS)


@app.route("/project-<string:project_name>.html")
def app_project(project_name: str) -> str:
    for project in PROJECTS:
        if project_name == project.stem:
            return render_template(
                "projects/" + project.stem + ".html", project=project
            )
    return render_template("projects.html", projects=PROJECTS)


@app.route("/about.html")
def app_about() -> str:
    return render_template("about.html")


@app.route("/featured.html")
def app_featured_images() -> str:
    return render_template("featured.html", featured_images=FEATURED_IMAGES)


@app.route("/requests.html")
def app_requests() -> str:
    return render_template(
        "request_list.html",
        requests=sorted(
            get_sub_requests(),
            key=lambda sub_request: sub_request.title.lower(),
        ),
    )


@app.route("/request_add.html", methods=["GET", "POST"])
def app_request_add() -> T.Any:
    title = request.form.get("title", "").strip()
    anidb_link = request.form.get("anidb_link", "").strip()
    comment = request.form.get("comment", "").strip()

    sub_requests = list(get_sub_requests())
    if request.headers.getlist("X-Forwarded-For"):
        remote_addr = request.headers.getlist("X-Forwarded-For")[0]
    else:
        remote_addr = request.remote_addr

    sub_request = SubRequest(
        title=title,
        date=datetime.now(),
        anidb_link=anidb_link,
        comment=comment,
        remote_addr=remote_addr,
    )

    errors: T.List[str] = []

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
            return redirect("requests.html", code=302)

    return render_template(
        "request_add.html", request=sub_request, errors=errors
    )


@app.route("/guest_book.html")
def app_guest_book() -> str:
    global GUEST_BOOK_CACHE
    if not GUEST_BOOK_CACHE or app.debug:
        GUEST_BOOK_CACHE = render_template(
            "guest_book.html",
            tid=GUEST_BOOK_TID,
            comments=[
                comment
                for comment in get_comments()
                if comment.tid == GUEST_BOOK_TID
            ],
        )
    return GUEST_BOOK_CACHE


@app.route("/comment_add.html", methods=["GET", "POST"])
def app_comment_add() -> T.Any:
    pid: int
    try:
        pid = int(request.args.get("pid", ""))
    except (TypeError, ValueError):
        pid = 0

    try:
        tid = int(request.args.get("tid", ""))
    except (TypeError, ValueError):
        tid = 0

    is_preview = request.form.get("submit") == "preview"
    text = request.form.get("text", "").strip()
    author = request.form.get("author", "").strip()
    website = request.form.get("website", "").strip()
    email = request.form.get("email", "").strip()

    comments = list(get_comments())
    parent_comment: T.Optional[Comment] = first(
        c for c in comments if c.id == pid
    )
    if parent_comment:
        tid = parent_comment.tid

    form_url = f"comment_add.html?tid={tid}&pid={pid}"

    if request.headers.getlist("X-Forwarded-For"):
        remote_addr = request.headers.getlist("X-Forwarded-For")[0]
    else:
        remote_addr = request.remote_addr

    id = max(comment.id for comment in comments) + 1 if comments else 0

    comment = Comment(
        tid=tid,
        id=id,
        pid=pid or None,
        created=datetime.now(),
        remote_addr=remote_addr,
        text=text,
        author=author,
        email=email,
        website=website,
        likes=0,
    )

    errors: T.List[str] = []

    if request.method == "POST":
        if request.form.get("phone") or request.form.get("message"):
            errors.append("Human verification failed.")
        if not comment.text:
            errors.append("Comment content cannot be empty.")
        if not comment.author:
            errors.append("Comment author cannot be empty.")
        if not comment.tid:
            errors.append("Comment thread ID cannot be empty.")

        if not errors and not is_preview:
            comments.insert(0, comment)
            save_comments(comments)
            global GUEST_BOOK_CACHE
            GUEST_BOOK_CACHE = ""
            return redirect("guest_book.html", code=302)

    return render_template(
        "comment_add.html",
        form_url=form_url,
        parent_comment=parent_comment,
        comment=comment,
        preview=is_preview,
        errors=errors,
    )
