"""Alibaba / Qwen update feed.

Aggregates five official update surfaces into one Feedseek feed:

- Alibaba Cloud Press Releases: https://www.alibabacloud.com/en/press-room/press-release
- Alibaba Cloud Product Updates: https://www.alibabacloud.com/en/news/product
- Alibaba Cloud Community Blog: https://www.alibabacloud.com/blog
- Qwen Research: https://qwen.ai/research
- QwenCloud News: https://www.qwencloud.com/news

The public pages use different layouts and some are client-heavy, so parsing is
semantic rather than CSS-class based. Link-backed cards are preferred; dated
cards without stable permalinks receive deterministic fragments on their source
listing page. One broken source never blocks the others.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from dataclasses import dataclass
from datetime import UTC
from typing import Any
from urllib.parse import urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from enrich import enrich_entries
from entry_identity import entry_id_for
from feedgen.feed import FeedGenerator
from utils import (
    add_entry_media,
    allocate_fair_share,
    dedupe_entries,
    deserialize_entries,
    load_cache,
    merge_entries,
    sanitize_xml,
    save_atom_feed,
    save_cache,
    setup_feed_extensions,
    setup_feed_links,
    setup_logging,
    sort_posts_for_feed,
)

logger = setup_logging()

FEED_NAME = "alibaba"
BLOG_URL = "https://www.alibabacloud.com/en/press-room/press-release"
MAX_ENTRIES = 300
DESC_LIMIT = 700

PRESS_URL = "https://www.alibabacloud.com/en/press-room/press-release"
PRODUCT_URL = "https://www.alibabacloud.com/en/news/product"
BLOG_INDEX_URL = "https://www.alibabacloud.com/blog"
QWEN_RESEARCH_URL = "https://qwen.ai/research"
QWENCLOUD_NEWS_URL = "https://www.qwencloud.com/news"

_DATE_RES = [
    re.compile(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s*\d{4}\b", re.I),
    re.compile(r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b"),
]


@dataclass(frozen=True)
class Source:
    key: str
    label: str
    url: str
    hosts: tuple[str, ...]
    path_prefixes: tuple[str, ...] = ()
    require_detail_path: bool = False


SOURCES = (
    Source(
        "press",
        "Alibaba Cloud Press",
        PRESS_URL,
        ("www.alibabacloud.com", "alibabacloud.com"),
        ("/en/press-room/",),
        True,
    ),
    Source(
        "product",
        "Alibaba Cloud Product Updates",
        PRODUCT_URL,
        ("www.alibabacloud.com", "alibabacloud.com"),
        ("/en/news/product/",),
        True,
    ),
    Source(
        "blog",
        "Alibaba Cloud Blog",
        BLOG_INDEX_URL,
        ("www.alibabacloud.com", "alibabacloud.com", "community.alibabacloud.com"),
        ("/blog/",),
        True,
    ),
    Source(
        "qwen-research",
        "Qwen Research",
        QWEN_RESEARCH_URL,
        ("qwen.ai", "www.qwen.ai"),
        ("/research/",),
        True,
    ),
    Source(
        "qwencloud",
        "QwenCloud News",
        QWENCLOUD_NEWS_URL,
        ("qwencloud.com", "www.qwencloud.com"),
        ("/news/",),
        True,
    ),
)


def doc_sources():
    """Return the official pages aggregated by this feed."""
    return [(source.label, source.url) for source in SOURCES]


def _get_html(url: str) -> str | None:
    """Fetch a public page with a browser fingerprint when available."""
    response: Any
    try:
        from curl_cffi import requests as creq

        response = creq.get(url, impersonate="chrome", timeout=30)
    except ImportError:
        try:
            response = requests.get(
                url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 Chrome/140.0 Safari/537.36"
                    )
                },
                timeout=30,
            )
        except requests.RequestException as exc:
            logger.warning("Fetch failed for %s: %s", url, exc)
            return None
    except Exception as exc:
        logger.warning("Fetch failed for %s: %s", url, exc)
        return None

    if response.status_code != 200:
        logger.warning("Fetch for %s returned HTTP %s", url, response.status_code)
        return None
    return response.text


def _clean(text: str | None) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _date_from_text(text: str):
    for pattern in _DATE_RES:
        match = pattern.search(text or "")
        if not match:
            continue
        try:
            parsed = date_parser.parse(match.group(0))
        except (ValueError, TypeError, OverflowError):
            continue
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
    return None


def _date_from_card(card):
    """Prefer explicit publication metadata before dates mentioned in body text."""
    if hasattr(card, "find_all"):
        for node in card.find_all("time"):
            value = node.get("datetime") or node.get_text(" ", strip=True)
            date_obj = _date_from_text(str(value))
            if date_obj:
                return date_obj

        for node in card.find_all(True):
            labels = " ".join(
                [
                    str(node.get("id") or ""),
                    *[str(value) for value in (node.get("class") or [])],
                ]
            ).lower()
            if not any(token in labels for token in ("date", "time", "publish", "update")):
                continue
            date_obj = _date_from_text(_clean(node.get_text(" ", strip=True)))
            if date_obj:
                return date_obj

    return _date_from_text(_clean(card.get_text(" ", strip=True)))


def _canonical_url(url: str) -> str:
    """Drop marketing query strings/fragments while preserving the canonical path."""
    parts = urlsplit(url)
    return urlunsplit((parts.scheme or "https", parts.netloc.lower(), parts.path, "", ""))


def _is_detail_link(source: Source, link: str) -> bool:
    parts = urlsplit(link)
    if (parts.hostname or "").lower() not in source.hosts:
        return False
    path = parts.path.rstrip("/")
    if source.path_prefixes and not any(path.startswith(prefix.rstrip("/")) for prefix in source.path_prefixes):
        return False
    if not source.require_detail_path:
        return True
    index_path = urlsplit(source.url).path.rstrip("/")
    return bool(path and path != index_path and path not in {"/en/press-room/press-release", "/blog", "/research"})


def _card(anchor):
    """Find the smallest semantic ancestor that contains a recognizable date."""
    fallback = anchor.parent or anchor
    for parent in anchor.parents:
        name = getattr(parent, "name", None)
        if name in {"main", "body", "html"}:
            break
        if name in {"article", "li"}:
            return parent
        text = _clean(parent.get_text(" ", strip=True))
        if len(text) <= 3000 and _date_from_text(text):
            return parent
        fallback = parent
    return fallback


def _title(card, anchor) -> str:
    for node in (card, anchor):
        if not hasattr(node, "find"):
            continue
        heading = node.find(["h1", "h2", "h3", "h4"])
        if heading:
            text = _clean(heading.get_text(" ", strip=True))
            if text:
                return text
    text = _clean(anchor.get_text(" ", strip=True))
    return text if len(text) >= 8 else ""


def _description(card, title: str) -> str:
    if not hasattr(card, "find_all"):
        return title
    for paragraph in card.find_all("p"):
        text = _clean(paragraph.get_text(" ", strip=True))
        if text and text != title and not _date_from_text(text):
            return text[:DESC_LIMIT]
    text = _clean(card.get_text(" ", strip=True))
    text = re.sub(re.escape(title), "", text, count=1).strip(" -—|")
    return text[:DESC_LIMIT] or title


def _image(card, page_url: str) -> str | None:
    if not hasattr(card, "find"):
        return None
    image = card.find("img")
    if not image:
        return None
    src = image.get("src") or image.get("data-src") or image.get("data-lazy-src")
    if not isinstance(src, str) or not src or src.startswith("data:"):
        return None
    return urljoin(page_url, src)


def _synthetic_link(source: Source, date_obj, title: str) -> str:
    digest = hashlib.sha256(title.encode("utf-8")).hexdigest()[:10]
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:64]
    stamp = date_obj.date().isoformat()
    return f"{source.url}#{source.key}-{stamp}-{slug}-{digest}"


def parse_source(html: str, source: Source) -> list[dict]:
    """Parse link-backed cards, then supplement with dated cards lacking permalinks."""
    soup = BeautifulSoup(html, "html.parser")
    entries = []
    seen = set()
    claimed_cards = set()

    for anchor in soup.find_all("a", href=True):
        raw_href = anchor.get("href", "")
        if not isinstance(raw_href, str):
            continue
        link = _canonical_url(urljoin(source.url, raw_href))
        if not _is_detail_link(source, link):
            continue
        card = _card(anchor)
        date_obj = _date_from_card(card)
        title = _title(card, anchor)
        if not date_obj or not title or link in seen:
            continue
        entries.append(
            {
                "title": sanitize_xml(title),
                "link": link,
                "date": date_obj,
                "description": sanitize_xml(_description(card, title)),
                "source": source.label,
                "image": _image(card, source.url),
            }
        )
        seen.add(link)
        claimed_cards.add(id(card))

    for text_node in soup.find_all(string=True):
        raw = _clean(str(text_node))
        trigger_date = _date_from_text(raw)
        if not trigger_date:
            continue
        card = _card(text_node.parent)
        date_obj = _date_from_card(card) or trigger_date
        if id(card) in claimed_cards:
            continue
        heading = card.find(["h1", "h2", "h3", "h4"]) if hasattr(card, "find") else None
        title = _clean(heading.get_text(" ", strip=True)) if heading else ""
        if not title:
            candidates = [
                _clean(value)
                for value in getattr(card, "stripped_strings", [])
                if _clean(value) and not _date_from_text(_clean(value))
            ]
            title = next((value for value in candidates if 8 <= len(value) <= 220), "")
        if not title:
            continue
        link = _synthetic_link(source, date_obj, title)
        if link in seen:
            continue
        entries.append(
            {
                "title": sanitize_xml(title),
                "link": link,
                "date": date_obj,
                "description": sanitize_xml(_description(card, title)),
                "source": source.label,
                "image": _image(card, source.url),
            }
        )
        seen.add(link)
        claimed_cards.add(id(card))

    return entries


def scrape_source(source: Source, known_links: set[str]) -> list[dict]:
    html = _get_html(source.url)
    if html is None:
        return []
    candidates = parse_source(html, source)
    if not candidates:
        logger.warning("[%s] no dated update cards matched", source.label)
        return []
    entries = [entry for entry in candidates if entry["link"] not in known_links]
    for entry in entries:
        logger.info("  [%s] %s", source.label, entry["title"])
    return entries


def scrape_all(known_links: set[str]) -> list[dict]:
    entries = []
    for source in SOURCES:
        logger.info("Scraping %s ...", source.label)
        entries.extend(scrape_source(source, known_links))
    return entries


def generate_atom_feed(articles: list[dict], feed_name: str = FEED_NAME):
    fg = FeedGenerator()
    fg.id("https://www.alibabacloud.com/")
    fg.title("Alibaba")
    fg.subtitle(
        "Alibaba Cloud press releases, product updates and blog posts, "
        "plus Qwen research and QwenCloud news."
    )
    setup_feed_links(fg, BLOG_URL, feed_name)
    setup_feed_extensions(fg)
    fg.language("en")
    fg.author({"name": "Alibaba Cloud / Qwen"})

    for article in articles:
        fe = fg.add_entry()
        fe.id(entry_id_for(feed_name, article))
        fe.title(article["title"])
        fe.link(href=article["link"])
        fe.description(article.get("description") or article["title"])
        fe.category(term=article["source"], label=article["source"])
        add_entry_media(fe, article.get("image"))
        if article.get("date"):
            fe.published(article["date"])
            fe.updated(article["date"])
    return fg


def main(full: bool = False) -> bool:
    cached = []
    if not full:
        cache = load_cache(FEED_NAME)
        cached = deserialize_entries(cache.get("entries", []), date_field="date")

    known_links = {entry["link"] for entry in cached}
    new_entries = scrape_all(known_links)

    if not new_entries and not cached:
        logger.warning("No Alibaba/Qwen updates collected; preserving any published feed")
        return False

    merged = merge_entries(new_entries, cached, id_field="link", date_field="date")
    merged = dedupe_entries(
        merged,
        id_field="link",
        title_field=None,
        date_field="date",
    )
    merged = sort_posts_for_feed(merged, date_field="date")
    feed_items = allocate_fair_share(merged, MAX_ENTRIES, date_field="date")

    enrich_entries(feed_items)
    save_cache(FEED_NAME, merged)
    save_atom_feed(generate_atom_feed(feed_items), FEED_NAME)
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate the Alibaba / Qwen feed")
    parser.add_argument("--full", action="store_true", help="Ignore cache and rebuild")
    args = parser.parse_args()
    sys.exit(0 if main(full=args.full) else 1)
