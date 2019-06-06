import typing as T

import bleach
import misaka

SAFE_ELEMENTS = [
    "a",
    "p",
    "hr",
    "br",
    "ol",
    "ul",
    "li",
    "pre",
    "code",
    "blockquote",
    "del",
    "ins",
    "strong",
    "em",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "table",
    "thead",
    "tbody",
    "th",
    "td",
]
SAFE_ATTRIBUTES = ["align", "href"]


def sanitize(text: str) -> str:
    clean_html = bleach.clean(
        text, tags=SAFE_ELEMENTS, attributes=SAFE_ATTRIBUTES, strip=True
    )

    def set_links(
        attrs: T.Dict[T.Tuple[T.Optional[str], str], str], new: bool = False
    ) -> T.Dict[T.Tuple[T.Optional[str], str], str]:
        href_key = (None, "href")

        if href_key not in attrs:
            return attrs
        if attrs[href_key].startswith("mailto:"):
            return attrs

        rel_key = (None, "rel")
        rel_values = [val for val in attrs.get(rel_key, "").split(" ") if val]

        for value in ["nofollow", "noopener"]:
            if value not in [rel_val.lower() for rel_val in rel_values]:
                rel_values.append(value)

        attrs[rel_key] = " ".join(rel_values)
        return attrs

    linker = bleach.linkifier.Linker(callbacks=[set_links])
    return linker.linkify(clean_html)


class Unofficial(misaka.HtmlRenderer):
    def blockcode(self, text: str, lang: T.Optional[str]) -> str:
        lang = ' class="{0}"'.format(lang) if lang else ""
        return "<pre><code{1}>{0}</code></pre>\n".format(text, lang)


def render_markdown(text: str) -> str:
    renderer = Unofficial()
    md = misaka.Markdown(
        renderer,
        extensions=("strikethrough", "autolink", "fenced-code"),
    )

    ret = md(text).rstrip("\n")
    if not (ret.startswith("<p>") or ret.endswith("</p>")):
        ret = "<p>" + ret + "</p>"
    ret = sanitize(ret)

    return ret
