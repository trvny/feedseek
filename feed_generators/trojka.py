#!/usr/bin/env python3
"""Generate an Atom feed for Program Trzeci Polskiego Radia."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from enrich import enrich_entries
from entry_identity import entry_id_for
from feedgen.feed import FeedGenerator
from utils import (
    add_entry_media,
    deserialize_entries,
    fetch_page,
    load_cache,
    localize_wall_time,
    merge_entries,
    sanitize_xml,
    save_atom_feed,
    save_cache,
    setup_feed_extensions,
    setup_feed_links,
    setup_logging,
    sort_posts_for_feed,
    stable_fallback_date,
)

logger = setup_logging()
FEED_NAME = "trojka"
SITE_URL = "https://trojka.polskieradio.pl"
BLOG_URL = SITE_URL
ICON_URL = "https://trojka.polskieradio.pl/assets/favicon-32x32.png"
# Redesign (Oct 2026): /czytaj-wiecej froze at 2026-09-28; articles now live on
# the home page and section pages, shipped as Next.js RSC flight data.
LISTING_PATHS = ("/", "/spoleczenstwo", "/kultura", "/muzyka", "/film")
_RSC_PUSH_RE = re.compile(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', re.DOTALL)
_RSC_ROW_RE = re.compile(r"^[0-9a-f]+:")


def _rsc_payload(html: str) -> str:
    chunks = _RSC_PUSH_RE.findall(html)
    if not chunks:
        raise ValueError("RSC flight data not found; page structure changed")
    return "".join(json.loads(f'"{chunk}"') for chunk in chunks)


def _walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from _walk(value)


def _article_objects(payload: str):
    """Yield article cards from flight rows ("<hex id>:<json>"): any object with
    id, href and publishDate, wherever it nests and whatever its key order."""
    for row in payload.split("\n"):
        match = _RSC_ROW_RE.match(row)
        if not match:
            continue
        try:
            tree = json.loads(row[match.end():])
        except ValueError:
            continue  # text/hint rows (T…, I[…], HL[…])
        for obj in _walk(tree):
            if obj.get("publishDate") and obj.get("href") and obj.get("id"):
                yield obj


def _article_link(href: str) -> str | None:
    """Trójka's own articles only; cross-promoted polskieradio24.pl cards are skipped."""
    if href.startswith("/"):
        return f"{SITE_URL}{href}"
    if href.startswith(f"{SITE_URL}/"):
        return href
    return None


def _parse_date(value: str | None, fallback_id: str) -> datetime:
    if not value:
        return stable_fallback_date(fallback_id)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = localize_wall_time(parsed, ZoneInfo("Europe/Warsaw"))
        return parsed
    except (ValueError, TypeError):
        logger.warning("Unable to parse date %r; using fallback", value)
        return stable_fallback_date(fallback_id)


def parse_posts(html: str, seen_ids: set[str] | None = None) -> list[dict]:
    seen_ids = set() if seen_ids is None else seen_ids
    posts: list[dict] = []
    for article in _article_objects(_rsc_payload(html)):
        try:
            if article["id"] in seen_ids or article.get("isSponsored"):
                continue
            link = _article_link(article["href"])
            title = (article.get("title") or article.get("mainTitle") or "").strip()
            if not link or not title:
                continue
            seen_ids.add(article["id"])
            clean_title = sanitize_xml(title)
            lead = sanitize_xml((article.get("lead") or article.get("description") or "").strip())
            posts.append(
                {
                    "link": link,
                    "title": clean_title,
                    "description": lead or clean_title,
                    "date": _parse_date(article.get("publishDate"), link),
                    "category": (article.get("category") or "").strip() or None,
                    "image": article.get("imageUrl"),
                }
            )
        except Exception as exc:
            logger.warning("Skipping malformed article (%s): %s", article.get("id"), exc)
    return posts


def fetch_posts() -> list[dict]:
    """Collect every listing page; one failing section does not sink the rest."""
    posts: list[dict] = []
    seen_ids: set[str] = set()
    for path in LISTING_PATHS:
        try:
            found = parse_posts(fetch_page(f"{SITE_URL}{path}"), seen_ids)
            logger.info("Parsed %d articles from %s", len(found), path)
            posts.extend(found)
        except Exception as exc:
            logger.warning("Trójka listing %s failed: %s", path, exc)
    return posts


def generate_atom_feed(posts: list[dict]) -> FeedGenerator:
    feed = FeedGenerator()
    feed.id("https://trojka.polskieradio.pl")
    feed.title("PR3 Trójka")
    feed.description(
        "Najnowsze artykuły radiowej Trójki: muzyka, kultura, koncerty, "
        "Lista Przebojów Trójki i Trójkowe podcasty."
    )
    feed.language("pl")
    feed.author({"name": "Polskie Radio – Trójka"})
    feed.logo(ICON_URL)
    feed.subtitle("Program Trzeci Polskiego Radia")
    setup_feed_links(
        feed,
        blog_url="https://trojka.polskieradio.pl",
        feed_name=FEED_NAME,
        icon=ICON_URL,
    )
    setup_feed_extensions(feed)

    for post in posts:
        entry = feed.add_entry()
        entry.title(post["title"])
        entry.description(post["description"])
        entry.link(href=post["link"])
        entry.id(entry_id_for(FEED_NAME, post))
        add_entry_media(entry, post.get("image"))
        if post.get("category"):
            entry.category(term=post["category"])
        if post.get("date"):
            entry.published(post["date"])
    return feed


def main(full_reset: bool = False) -> bool:
    try:
        cached = deserialize_entries(load_cache(FEED_NAME).get("entries", []))
        new_posts = fetch_posts()
    except Exception as exc:
        logger.error("Trójka fetch/parse failed: %s", exc)
        return False
    if not new_posts:
        logger.error("No Trójka articles parsed from any listing; keeping the last good feed")
        return False

    if full_reset or not cached:
        posts = sort_posts_for_feed(new_posts, date_field="date")
    else:
        posts = merge_entries(new_posts, cached)

    enrich_entries(posts)
    if not posts:
        logger.warning("No posts fetched; keeping the last good feed")
        return False

    save_cache(FEED_NAME, posts)
    save_atom_feed(generate_atom_feed(posts), FEED_NAME)
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Trójka Atom feed")
    parser.add_argument("--full", action="store_true", help="Ignore cache and rebuild")
    sys.exit(0 if main(full_reset=parser.parse_args().full) else 1)
