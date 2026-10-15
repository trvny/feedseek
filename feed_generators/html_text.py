"""Shared HTML detection and plaintext extraction for generated feeds.

This module is the single maintained HTML vocabulary for JSON Feed repair,
Model Feed normalization, and other Python-side feed adapters. It deliberately
recognizes real HTML elements while leaving type-like text such as List<T>
alone.
"""

from __future__ import annotations

import html as html_lib
import re
from html.parser import HTMLParser

BLOCK_TAGS = {
    "address", "article", "aside", "blockquote", "br", "caption", "dd",
    "details", "dialog", "div", "dl", "dt", "fieldset", "figcaption",
    "figure", "footer", "form", "h1", "h2", "h3", "h4", "h5", "h6",
    "header", "hgroup", "hr", "legend", "li", "main", "menu", "nav", "ol",
    "p", "pre", "section", "summary", "table", "tbody", "td", "tfoot",
    "th", "thead", "tr", "ul",
}
SKIP_TAGS = {"script", "style", "template"}
HTML_TAGS = BLOCK_TAGS | SKIP_TAGS | {
    "a", "abbr", "area", "audio", "b", "base", "bdi", "bdo", "body",
    "button", "canvas", "center", "cite", "code", "col", "colgroup", "data",
    "datalist", "del", "dfn", "em", "embed", "font", "head", "html", "i",
    "iframe", "img", "input", "ins", "kbd", "label", "link", "map", "mark",
    "meta", "meter", "noscript", "object", "optgroup", "option", "output",
    "picture", "progress", "q", "rp", "rt", "ruby", "s", "samp", "search",
    "select", "slot", "small", "source", "span", "strong", "sub", "sup",
    "textarea", "time", "title", "track", "u", "var", "video", "wbr",
}


class _HTMLProbe(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.found = False

    def handle_starttag(self, tag: str, attrs) -> None:
        del attrs
        if tag.lower() in HTML_TAGS:
            self.found = True

    def handle_startendtag(self, tag: str, attrs) -> None:
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in HTML_TAGS:
            self.found = True


def looks_like_html(value: str) -> bool:
    """Return true only when value contains a recognized HTML element."""
    if "<" not in value or ">" not in value:
        return False
    parser = _HTMLProbe()
    try:
        parser.feed(value)
        parser.close()
    except Exception:
        return False
    return parser.found


class _HTMLTextExtractor(HTMLParser):
    """Extract rendered text while preserving whitespace inside pre."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[tuple[bool, str]] = []
        self.skip_depth = 0
        self.pre_depth = 0

    def _break(self) -> None:
        if not self.skip_depth:
            self.parts.append((False, "\n\n"))

    def handle_starttag(self, tag: str, attrs) -> None:
        del attrs
        name = tag.lower()
        if name not in HTML_TAGS:
            return
        if name in SKIP_TAGS:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        if name in BLOCK_TAGS:
            self._break()
        if name == "pre":
            self.pre_depth += 1

    def handle_startendtag(self, tag: str, attrs) -> None:
        name = tag.lower()
        self.handle_starttag(tag, attrs)
        if name in SKIP_TAGS and self.skip_depth:
            self.skip_depth -= 1

    def handle_endtag(self, tag: str) -> None:
        name = tag.lower()
        if name not in HTML_TAGS:
            return
        if name in SKIP_TAGS:
            if self.skip_depth:
                self.skip_depth -= 1
            return
        if self.skip_depth:
            return
        if name == "pre" and self.pre_depth:
            self.pre_depth -= 1
        if name in BLOCK_TAGS:
            self._break()

    def handle_data(self, data: str) -> None:
        if not self.skip_depth:
            self.parts.append((self.pre_depth > 0, data))


def _render_parts(parts: list[tuple[bool, str]]) -> str:
    out: list[tuple[bool, str]] = []
    for is_pre, value in parts:
        value = value.replace("\r\n", "\n").replace("\r", "\n")
        if is_pre:
            if value:
                out.append((True, value))
            continue

        if value == "\n\n":
            if not out:
                continue
            if not out[-1][0]:
                out[-1] = (False, out[-1][1].rstrip(" "))
            current = out[-1][1]
            if current.endswith("\n\n"):
                continue
            out.append((False, "\n" if current.endswith("\n") else "\n\n"))
            continue

        normalized = re.sub(r"\s+", " ", value)
        if out and out[-1][1].endswith("\n"):
            normalized = normalized.lstrip(" ")
        if normalized:
            out.append((False, normalized))

    return "".join(value for _, value in out).strip("\n")


def html_to_text(value: str) -> str:
    """Render known HTML to plaintext without recursive entity decoding."""
    parser = _HTMLTextExtractor()
    parser.feed(value.replace("\r\n", "\n").replace("\r", "\n"))
    parser.close()
    return _render_parts(parser.parts)


def plain_text(value: object, *, html_hint: bool = False) -> str:
    """Normalize one value while preserving literal markup and code layout."""
    if not isinstance(value, str) or not value.strip():
        return ""

    raw = value.replace("\r\n", "\n").replace("\r", "\n")
    if html_hint or looks_like_html(raw):
        return html_to_text(raw)

    # Plaintext may still contain escaped entities from an upstream feed. Decode
    # them once, but never feed the decoded result back into the HTML parser.
    return html_lib.unescape(raw).strip()
