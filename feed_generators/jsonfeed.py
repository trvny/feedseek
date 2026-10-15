"""JSON Feed 1.1 sidecar writer.

Every feed this project publishes as ``feeds/feed_<name>.xml`` also gets a
``feeds/feed_<name>.json`` sibling in JSON Feed 1.1 format
(https://jsonfeed.org/version/1.1). It is written from the just-produced XML
so the published Atom/RSS file stays the single source of truth — whatever the
generator emitted (MRSS media, dc:creator, tag-URI ids) is mirrored, not
re-derived. XML readers can still ignore the .json, but both representations are
first-class publication artifacts.

The private ``_feedseek`` extension records where the selected text came
from. It follows JSON Feed's extension naming rules and points readers to its
human-readable documentation. Dedicated Feedseek Model Feeds use that hint
without changing the standard JSON Feed content fields.

Called from ``utils.save_atom_feed`` / ``utils.save_rss_feed``. If sidecar
serialization fails after XML rendering, the shared writer restores the previous
publication set so scheduled updates remain last-known-good.
"""

import calendar
import json
from datetime import datetime, timezone
from pathlib import Path

from html_text import looks_like_html
from utils import REPO_SLUG, large_icon, write_atomically

JSON_FEED_VERSION = "https://jsonfeed.org/version/1.1"

# Same rel=self base the Atom writer uses (utils.setup_feed_links), pointing at
# the JSON sibling instead of the .xml.
_FEED_URL_TMPL = (
    f"https://raw.githubusercontent.com/{REPO_SLUG}/main/feeds/feed_{{name}}.json"
)

def _rfc3339(struct_time) -> str | None:
    """Convert a feedparser UTC struct_time to an RFC 3339 / ISO 8601 string."""
    if not struct_time:
        return None
    try:
        dt = datetime.fromtimestamp(calendar.timegm(struct_time), tz=timezone.utc)
    except (TypeError, ValueError, OverflowError):
        return None
    return dt.isoformat().replace("+00:00", "Z")


def _entry_content(entry) -> tuple[str, str, str]:
    """Return ``(json_feed_key, value, text_kind)``.

    Upstreams occasionally label HTML descriptions as plain text (Google News
    is a common example). Detect recognizable markup so JSON Feed semantics stay
    truthful. When no body or summary exists, use the title rather than publish
    a structurally valid but useless empty content field.
    """
    for content in entry.get("content") or []:
        value = (content.get("value") or "").strip()
        if not value:
            continue
        declared_type = (content.get("type") or "").lower()
        if declared_type.endswith(("html", "xhtml")) or looks_like_html(value):
            return "content_html", value, "content"
        return "content_text", value, "content"

    summary = (entry.get("summary") or "").strip()
    if summary:
        declared_type = (entry.get("summary_detail") or {}).get("type", "").lower()
        if declared_type.endswith(("html", "xhtml")) or looks_like_html(summary):
            return "content_html", summary, "summary"
        return "content_text", summary, "summary"

    title = (entry.get("title") or "").strip()
    return "content_text", title, "title"


def build_json_feed(xml_path: Path, feed_name: str, entry_image=None) -> dict:
    """Parse the written feed_<name>.xml and return a JSON Feed 1.1 dict.

    ``entry_image`` is an optional callable (utils.feedparser_entry_image) used
    to lift a per-item image from MRSS/enclosure data.
    """
    import feedparser  # local import: keeps utils import-time light

    parsed = feedparser.parse(str(xml_path))
    feed = parsed.feed

    doc: dict = {
        "version": JSON_FEED_VERSION,
        "title": feed.get("title") or feed_name,
        "feed_url": _FEED_URL_TMPL.format(name=feed_name),
        "_feedseek": {
            "about": "https://trvny.github.io/feedseek/llms-full.txt"
        },
    }
    if feed.get("link"):
        doc["home_page_url"] = feed["link"]
    if feed.get("subtitle"):
        doc["description"] = feed["subtitle"]
    if feed.get("icon"):
        doc["favicon"] = feed["icon"]
    if feed.get("logo") or feed.get("icon"):
        # JSON Feed splits these: "favicon" is the small square, "icon" is the
        # big one a reader puts on a card. Serving the 64px image as both wastes
        # the distinction, so upscale when the icon host can serve a larger one.
        doc["icon"] = large_icon(feed.get("logo") or feed["icon"])

    items = []
    for entry in parsed.entries:
        item: dict = {"id": entry.get("id") or entry.get("link") or ""}
        if entry.get("link"):
            item["url"] = entry["link"]
        if entry.get("title"):
            item["title"] = entry["title"]

        content_key, content_value, text_kind = _entry_content(entry)
        item[content_key] = content_value
        item["_feedseek"] = {"textKind": text_kind}

        if published := _rfc3339(entry.get("published_parsed")):
            item["date_published"] = published
        if modified := _rfc3339(entry.get("updated_parsed")):
            item["date_modified"] = modified

        if entry.get("author"):
            item["authors"] = [{"name": entry["author"]}]

        if entry_image and (image := entry_image(entry)):
            item["image"] = image

        if tags := [
            tag.get("term")
            for tag in (entry.get("tags") or [])
            if tag.get("term")
        ]:
            item["tags"] = tags

        attachments = []
        for enclosure in entry.get("enclosures") or []:
            href = enclosure.get("href")
            if not href:
                continue
            attachment = {
                "url": href,
                "mime_type": enclosure.get("type") or "application/octet-stream",
            }
            length = enclosure.get("length")
            if length and str(length).isdigit() and int(length) > 0:
                attachment["size_in_bytes"] = int(length)
            attachments.append(attachment)
        if attachments:
            item["attachments"] = attachments

        items.append(item)

    doc["items"] = items
    return doc


def write_json_feed(xml_path: Path, feed_name: str, entry_image=None) -> Path:
    """Write feeds/feed_<name>.json next to the given XML path. Returns the path."""
    doc = build_json_feed(xml_path, feed_name, entry_image=entry_image)
    out = xml_path.with_suffix(".json")
    payload = json.dumps(doc, ensure_ascii=False, indent=2) + "\n"
    write_atomically(out, lambda target: target.write_text(payload, encoding="utf-8"))
    return out
