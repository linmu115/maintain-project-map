"""Mistune Markdown with project-owned link routing and scoped heading anchors."""
from __future__ import annotations

import hashlib
import html
import re
from urllib.parse import urlsplit

import mistune


def plain_text(rendered: str) -> str:
    return html.unescape(re.sub(r"<[^>]*>", "", rendered))


def heading_slug(title: str) -> str:
    return re.sub(r"[^\w\- ]", "", title.strip().lower()).replace(" ", "-")


def anchor_id(scope: str, anchor: str) -> str:
    return "section-" + hashlib.sha256(scope.encode()).hexdigest()[:12] + "-" + anchor


def wiki_links(md):
    # This extension only recognizes the notation. Resolution, identity and
    # ambiguity belong to the map index, just as normal relative links do.
    def parse(inline, match, state):
        value = match.group("project_wiki_target")
        target, separator, label = value.partition("|")
        state.append_token({"type": "project_wiki_link", "raw": (label if separator else target).strip(),
                            "attrs": {"url": target.strip()}})
        return match.end()

    md.inline.register("project_wiki_link", r"(?<!!)\[\[(?P<project_wiki_target>[^\]\n]+)\]\]", parse, before="link")


class ReaderRenderer(mistune.HTMLRenderer):
    def __init__(self, resolve_link=None, scope=""):
        super().__init__(escape=True)
        self.resolve_link, self.scope = resolve_link, scope
        self.seen, self.anchors = {}, set()

    def heading(self, text, level, **attrs):
        slug = heading_slug(plain_text(text))
        suffix = self.seen.get(slug, 0)
        self.seen[slug] = suffix + 1
        slug += f"-{suffix}" if suffix else ""
        self.anchors.add(slug)
        attributes = (' id="' + html.escape(anchor_id(self.scope, slug), quote=True)
                      + '" data-anchor="' + html.escape(slug, quote=True) + '"') if self.scope else ""
        n = min(6, level + 1)
        return f"<h{n}{attributes}>" + text + f"</h{n}>\n"

    def link(self, text, url, title=None):
        try:
            parsed = urlsplit(url)
        except ValueError:
            return text + ' <code class="link-locator">' + html.escape(url) + '</code>'
        if parsed.scheme.lower() in {"http", "https"} and parsed.netloc:
            return ('<a href="' + html.escape(url, quote=True) + '" target="_blank" rel="noopener noreferrer">'
                    + text + '</a>')
        if self.resolve_link and (link := self.resolve_link(plain_text(text), url)):
            return link
        return text + ' <code class="link-locator">' + html.escape(url) + '</code>'

    def project_wiki_link(self, text, url):
        if self.resolve_link and (link := self.resolve_link(text, url, wiki=True)):
            return link
        return '<span class="unresolved-link" title="没有唯一匹配的地图记录或已收录资料">' + html.escape(text) + '</span>'

    def image(self, text, url, title=None):
        # Images are not fetched by this offline reader; native diagrams have
        # their own declared asset/export pipeline.
        return html.escape(plain_text(text)) + ' <code class="link-locator">' + html.escape(url) + '</code>'


def markdown_html(source: str, resolve_link=None, scope: str = "") -> str:
    renderer = ReaderRenderer(resolve_link, scope)
    return mistune.create_markdown(renderer=renderer, plugins=["table", "strikethrough", wiki_links])(str(source))


def heading_anchors(source: str) -> set[str]:
    renderer = ReaderRenderer()
    mistune.create_markdown(renderer=renderer, plugins=["table", "strikethrough", wiki_links])(str(source))
    return renderer.anchors
