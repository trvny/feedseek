"""Xweather blog + product changelog feed.

Combines the public Xweather blog with the requested product changelogs. Each
source is fetched independently so one broken documentation surface does not
block the rest of the feed.
"""

import argparse
import re
import sys
from datetime import UTC
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from feedgen.feed import FeedGenerator

from utils import (
    deserialize_entries,
    fetch_page,
    load_cache,
    merge_entries,
    sanitize_xml,
    save_atom_feed,
    save_cache,
    setup_feed_links,
    setup_logging,
    sort_posts_for_feed,
    stable_fallback_date,
)

logger = setup_logging()

FEED_NAME = "xweather_log"
BLOG_URL = "https://www.xweather.com/blog"

SOURCES = [
    ("Xweather Blog", BLOG_URL),
    ("Weather API", "https://www.xweather.com/docs/weather-api/changelog"),
    ("MCP Server", "https://www.xweather.com/docs/mcp-server/changelog"),
    ("Android SDK", "https://www.xweather.com/docs/android-sdk/changelog"),
    ("Maps UI SDK", "https://www.xweather.com/docs/maps-ui-sdk/changelog"),
    ("Webhooks", "https://www.xweather.com/docs/webhooks/changelog"),
    ("MapsGL", "https://www.xweather.com/docs/mapsgl/changelog"),
    ("Phrases API", "https://www.xweather.com/docs/phrases-api/changelog"),
]

MAX_ENTRIES = 250
_DATE_RE = re.compile(
    r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|"
    r"Dec(?:ember)?)\s+\d{1,2},\s+\d{4}\b",
    re.IGNORECASE,
)
_VERSION_RE = re.compile(r"^v?\d+(?:\.\d+)+(?:[-+][0-9A-Za-z.-]+)?$")


def fetch_text(url: str):
    """Fetch one Xweather page without letting a single source sink the run."""
    try:
        return fetch_page(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (compatible; Feedseek/1.0; "
                    "+https://github.com/trvny/feedseek)"
                )
            },
        )
    except Exception as exc:
        logger.warning("Fetch failed for %s: %s", url, exc)
        return None


def parse_date(value: str | None):
    if not value:
        return None
    try:
        dt = date_parser.parse(value, fuzzy=True)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)
    except (TypeError, ValueError, OverflowError):
        return None


def _absolute_blog_link(href: str) -> str | None:
    link = urljoin(BLOG_URL, href)
    parts = urlparse(link)
    if parts.netloc not in {"xweather.com", "www.xweather.com"}:
        return None
    path = parts.path.rstrip("/")
    if not path.startswith("/blog/") or path.startswith("/blog/category/"):
        return None
    return f"https://www.xweather.com{path}"


def _article_container(anchor):
    """Find the smallest ancestor carrying both a title and a publication date."""
    node = anchor
    for _ in range(8):
        node = getattr(node, "parent", None)
        if node is None:
            break
        text = node.get_text(" ", strip=True)
        if _DATE_RE.search(text) and node.find(["h1", "h2", "h3", "h4"]):
            return node
    return anchor.parent


def parse_blog(html: str) -> list[dict]:
    """Parse server-rendered Xweather blog cards."""
    soup = BeautifulSoup(html, "html.parser")
    entries = []
    seen = set()

    for anchor in soup.find_all("a", href=True):
        link = _absolute_blog_link(anchor["href"])
        if not link or link in seen:
            continue

        container = _article_container(anchor)
        heading = container.find(["h1", "h2", "h3", "h4"]) if container else None
        anchor_text = anchor.get_text(" ", strip=True)
        title = heading.get_text(" ", strip=True) if heading else anchor_text
        if not title or title.lower() in {"learn more", "read more", "view all"}:
            continue

        text = container.get_text(" ", strip=True) if container else ""
        date_match = _DATE_RE.search(text)
        date = parse_date(date_match.group(0)) if date_match else None

        category = "Blog"
        if container:
            category_anchor = container.find(
                "a",
                href=re.compile(
                    r"^/blog/category/|^https?://(?:www\.)?xweather\.com/blog/category/"
                ),
            )
            if category_anchor:
                label = category_anchor.get_text(" ", strip=True)
                if label:
                    category = label

        description = title
        if container:
            paragraph = container.find("p")
            if paragraph:
                body = sanitize_xml(paragraph.get_text(" ", strip=True))
                if body:
                    description = body[:1200]

        seen.add(link)
        entries.append(
            {
                "title": sanitize_xml(title),
                "link": link,
                "date": date or stable_fallback_date(link),
                "description": description,
                "content_type": "text",
                "source": "Xweather Blog",
                "category": category,
            }
        )

    logger.info("[Blog] parsed %d articles", len(entries))
    return entries


def _heading_fragment(h2, version: str) -> str:
    if h2.get("id"):
        return h2["id"]
    nested = h2.find("a", href=re.compile(r"^#"))
    if nested and nested.get("href"):
        return nested["href"].lstrip("#")
    return re.sub(r"[^a-z0-9-]+", "", version.lower())


def parse_changelog(html: str, label: str, url: str) -> list[dict]:
    """Parse version/date/body groups from an Xweather documentation changelog."""
    soup = BeautifulSoup(html, "html.parser")
    root = soup.find("main") or soup
    entries = []

    for h2 in root.find_all("h2"):
        version = h2.get_text(" ", strip=True)
        if not _VERSION_RE.fullmatch(version):
            continue

        date = None
        body_parts = []
        for node in h2.find_all_next(["h2", "h3", "p", "li", "time"], limit=120):
            if node is h2:
                continue
            if node.name == "h2":
                break

            text = node.get_text(" ", strip=True)
            if not text:
                continue

            if date is None:
                match = _DATE_RE.search(text)
                if match:
                    date = parse_date(match.group(0))
                    if text == match.group(0):
                        continue

            if node.name == "h3":
                body_parts.append(f"{text}:")
            elif node.name in {"p", "li"}:
                if node.find_parent(["p", "li"]) is not None:
                    continue
                body_parts.append(text)

        fragment = _heading_fragment(h2, version)
        link = f"{url}#{fragment}" if fragment else url
        description = sanitize_xml(" ".join(body_parts)[:3000]) or f"{label} {version}"

        entries.append(
            {
                "title": sanitize_xml(f"{label} {version}"),
                "link": link,
                "date": date or stable_fallback_date(f"{url}:{version}"),
                "description": description,
                "content_type": "text",
                "source": f"Xweather {label}",
                "category": label,
            }
        )

    logger.info("[%s] parsed %d releases", label, len(entries))
    return entries


def collect_source(label: str, url: str) -> list[dict]:
    html = fetch_text(url)
    if html is None:
        return []
    if url == BLOG_URL:
        return parse_blog(html)
    return parse_changelog(html, label, url)


def generate_atom_feed(entries):
    fg = FeedGenerator()
    fg.id("https://www.xweather.com/")
    fg.title("Xweather Log")
    fg.subtitle("Xweather blog posts and product changelogs in one feed.")
    setup_feed_links(fg, BLOG_URL, FEED_NAME)
    fg.language("en")
    fg.author({"name": "Xweather"})

    for entry in entries:
        fe = fg.add_entry()
        fe.id(entry["link"])
        fe.title(entry["title"])
        fe.link(href=entry["link"])
        fe.content(entry["description"], type=entry.get("content_type", "text"))
        if entry.get("source"):
            fe.author({"name": entry["source"]})
        if entry.get("category"):
            fe.category(term=entry["category"])
        if entry.get("date"):
            fe.published(entry["date"])
            fe.updated(entry["date"])

    return fg


def main(full=False):
    if full:
        cached = []
    else:
        cache = load_cache(FEED_NAME)
        cached = deserialize_entries(cache.get("entries", []), date_field="date")

    new_entries = []
    for label, url in SOURCES:
        new_entries.extend(collect_source(label, url))

    if not new_entries:
        logger.error("All Xweather sources failed; preserving the last good feed")
        return False

    merged = merge_entries(new_entries, cached, id_field="link", date_field="date")
    if not merged:
        logger.warning("No Xweather entries; skipping empty output")
        return False

    merged = sort_posts_for_feed(merged, date_field="date")
    if len(merged) > MAX_ENTRIES:
        merged = merged[-MAX_ENTRIES:]

    save_cache(FEED_NAME, merged)
    save_atom_feed(generate_atom_feed(merged), FEED_NAME)
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate the Xweather blog + product changelog Atom feed"
    )
    parser.add_argument(
        "--full", action="store_true", help="Ignore cache and rebuild from scratch"
    )
    sys.exit(0 if main(full=parser.parse_args().full) else 1)
