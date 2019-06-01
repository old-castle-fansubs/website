import typing as T

import arrow
import werkzeug.routing
from flask import (
    Flask,
    Response,
    redirect,
    request,
    send_from_directory,
    render_template,
)

from oc_website.lib.comments import Comment, get_comments, save_comments
from oc_website.lib.common import STATIC_DIR, first
from oc_website.lib.env import ProjectLoader, get_env
from oc_website.lib.featured_images import get_featured_images
from oc_website.lib.news import get_news
from oc_website.lib.projects import get_projects
from oc_website.lib.releases import get_releases
from oc_website.lib.thumbnails import generate_thumbnail

app = Flask(__name__)
app.jinja_env = get_env()

FEATURED_IMAGES = list(get_featured_images())
PROJECTS = list(sorted(get_projects(), key=lambda project: project.title))
NEWS = sorted(get_news(), key=lambda news: news.path, reverse=True)
RELEASES = list(get_releases())

GUEST_BOOK_CACHE: T.Optional[str] = None
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
    '/<regex(".*\\.css|img(-thumb)?/.*|favicon\\.ico|robots\\.txt"):path>'
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
    return render_template("news.html", news_entries=NEWS)


@app.route("/projects.html")
def app_projects() -> str:
    return render_template("projects.html", projects=PROJECTS)


@app.route("/project-<string:project_name>.html")
def app_project(project_name: str) -> str:
    for project in PROJECTS:
        if project_name in project.url:
            ProjectLoader.source = project.content
            return render_template(
                "project.html",
                project=project,
                releases=RELEASES,
            )
    return render_template("projects.html", projects=PROJECTS)


@app.route("/about.html")
def app_about() -> str:
    return render_template("about.html")


@app.route("/featured.html")
def app_featured_images() -> str:
    return render_template("featured.html", featured_images=FEATURED_IMAGES)


@app.route("/guest_book.html")
def app_guest_book() -> str:
    global GUEST_BOOK_CACHE
    if not GUEST_BOOK_CACHE:
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
def app_comment_add() -> T.Union[str, Response]:
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
    content = request.form.get("content", "")
    author = request.form.get("author", "")
    website = request.form.get("website", "")
    email = request.form.get("email", "")

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
        created=arrow.now(),
        remote_addr=remote_addr,
        text=content,
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
            GUEST_BOOK_CACHE = None
            return redirect("guest_book.html", code=302)

    return render_template(
        "comment_add.html",
        form_url=form_url,
        parent_comment=parent_comment,
        comment=comment,
        preview=is_preview,
        errors=errors,
    )
