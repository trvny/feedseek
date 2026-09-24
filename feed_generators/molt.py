"""Combined Molt ecosystem feed.

Moltbook hot posts come from the public JSON API, while SpaceMolt news and
changelog entries come from their native feeds. Moltbook pagination fills a
bounded hot window before shared cache state advances. Publication then uses the
shared fair-share allocator across submolts and the two official SpaceMolt streams.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from urllib.parse import quote

from multi_rss import get_html, parse_date, run, scrape_feed
from utils import sanitize_xml, setup_logging

logger = setup_logging()

FEED_NAME = "molt"
SOURCE_NAME = "Moltbook"
MOLTBOOK_SITE_URL = "https://www.moltbook.com/"
SITE_URL = MOLTBOOK_SITE_URL
MOLTBOOK_PAGE_SIZE = 25
MOLTBOOK_HOT_WINDOW = 25
MOLTBOOK_API_URL = (
    f"https://www.moltbook.com/api/v1/posts?sort=hot&limit={MOLTBOOK_PAGE_SIZE}"
)
SPACEMOLT_SOURCES = (
    ("SpaceMolt News", "https://spacemolt.com/news/feed.xml", 40),
    ("SpaceMolt Changelog", "https://spacemolt.com/changelog/rss.xml", 40),
)
SPACEMOLT_NATIVE_SOURCES = (SPACEMOLT_SOURCES[0],)
SPACEMOLT_CHANGELOG_PAGE = "https://spacemolt.com/changelog"
MAX_ENTRIES = 250
CANDIDATE_LIMIT = 1000
OFFICIAL_STREAM_CAP = 30
PER_STREAM_CAP = {
    "": 20,
    "SpaceMolt News": OFFICIAL_STREAM_CAP,
    "SpaceMolt Changelog": OFFICIAL_STREAM_CAP,
}
CANDIDATE_SOURCE_RESERVE = {
    label: OFFICIAL_STREAM_CAP for label, _url, _fetch_cap in SPACEMOLT_SOURCES
}
ALLOCATION_FIELD = "submolt"


def doc_sources():
    """Expose all concrete upstream endpoints used by the combined feed."""
    return [
        ("SpaceMolt News", SPACEMOLT_SOURCES[0][1]),
        ("SpaceMolt Changelog", SPACEMOLT_SOURCES[1][1]),
        ("Moltbook Posts API", MOLTBOOK_API_URL),
    ]


def _parse_date(value) -> datetime | None:
    """Parse a Moltbook timestamp through Feedseek's shared safe date parser."""
    return parse_date(value) if value else None


def _spacemolt_changelog_link(entry: dict) -> str:
    """Give SpaceMolt releases the unique fragment carried by their RSS GUID."""
    match = re.search(r"\bv(\d+(?:\.\d+)+)\b", str(entry.get("title") or ""))
    if match:
        return f"{SPACEMOLT_CHANGELOG_PAGE}#v{match.group(1)}"
    return str(entry.get("link") or "").strip()


def scrape_spacemolt_changelog(known_links: set[str]) -> list[dict]:
    """Keep changelog releases distinct even though their RSS <link> is shared."""
    label, feed_url, cap = SPACEMOLT_SOURCES[1]
    entries = scrape_feed(label, feed_url, set(), cap=cap)
    fresh: list[dict] = []
    for entry in entries:
        link = _spacemolt_changelog_link(entry)
        if not link or link in known_links:
            continue
        normalized = entry.copy()
        normalized["link"] = link
        fresh.append(normalized)
    return fresh


def _post_link(post: dict) -> str:
    """Return the canonical Moltbook web URL for an API post."""
    post_id = str(post.get("id") or "").strip()
    return f"{MOLTBOOK_SITE_URL}post/{post_id}" if post_id else ""


def _post_submolt(post: dict) -> str:
    """Return the post's submolt as a readable description label."""
    submolt = post.get("submolt")
    if isinstance(submolt, dict):
        name = submolt.get("name") or submolt.get("display_name")
    else:
        name = submolt
    return sanitize_xml(f"m/{str(name or 'unknown').strip()}")


def _restore_submolt(entry: dict) -> dict:
    """Backfill the submolt bucket on legacy Moltbook cache entries only."""
    if entry.get(ALLOCATION_FIELD) or entry.get("source") != SOURCE_NAME:
        return entry
    migrated = entry.copy()
    match = re.search(r"\bm/[\w.-]+", str(entry.get("description") or ""))
    migrated[ALLOCATION_FIELD] = sanitize_xml(match.group(0)) if match else "m/unknown"
    return migrated


def _post_description(post: dict) -> str:
    """Build a compact description with author, submolt and engagement."""
    author = post.get("author")
    author_name = author.get("name") if isinstance(author, dict) else author
    author_name = sanitize_xml(str(author_name or "unknown agent").strip())
    score = post.get("score", post.get("upvotes", 0))
    comments = post.get("comment_count", 0)
    header = (
        f"{author_name} · {_post_submolt(post)} · score {score} · {comments} comments"
    )

    body = sanitize_xml(" ".join(str(post.get("content") or "").split()))[:1400]
    external = str(post.get("url") or "").strip()
    parts = [header]
    if body:
        parts.append(body)
    if external:
        parts.append(f"Link: {external}")
    return "\n\n".join(parts)


def _post_title(post: dict) -> str:
    """Return a feed-safe title, or an empty string when sanitization removes it."""
    return sanitize_xml(str(post.get("title") or "").strip()).strip()


def _usable_post(post) -> bool:
    """Return whether a raw API post is eligible for the published feed."""
    return bool(
        isinstance(post, dict)
        and not post.get("is_deleted")
        and not post.get("is_spam")
        and _post_link(post)
        and _post_title(post)
    )


def parse_posts(payload: dict, known_links: set[str]) -> list[dict]:
    """Normalize Moltbook API posts into Feedseek entry dictionaries."""
    if not isinstance(payload, dict):
        return []
    posts = payload.get("posts")
    if not isinstance(posts, list):
        return []

    entries: list[dict] = []
    for post in posts:
        if not _usable_post(post):
            continue
        link = _post_link(post)
        if link in known_links:
            continue
        entries.append(
            {
                "title": _post_title(post),
                "link": link,
                "date": _parse_date(post.get("created_at")),
                "description": _post_description(post),
                "source": SOURCE_NAME,
                ALLOCATION_FIELD: _post_submolt(post),
            }
        )
    return entries


def _decode_page(raw: str | None, url: str) -> dict | None:
    """Decode one posts API page, isolating malformed or failed responses."""
    if raw is None:
        return None
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.warning("[Moltbook] invalid API JSON from %s: %s", url, exc)
        return None
    if not isinstance(payload, dict) or not payload.get("success", True):
        logger.warning("[Moltbook] API returned an unusable page for %s", url)
        return None
    return payload


def _page_url(cursor: str | None) -> str:
    """Build a cursor-safe URL for one Moltbook posts page."""
    if not cursor:
        return MOLTBOOK_API_URL
    return f"{MOLTBOOK_API_URL}&cursor={quote(cursor, safe='')}"


def _load_page(cursor: str | None, fetch) -> tuple[list, str | None, bool] | None:
    """Fetch and validate one cursor page, returning posts and continuation state."""
    url = _page_url(cursor)
    payload = _decode_page(fetch(url, retry_delay=2), url)
    if payload is None:
        return None
    posts = payload.get("posts")
    if not isinstance(posts, list):
        logger.warning("[Moltbook] API page has no posts list: %s", url)
        return None
    next_cursor = str(payload.get("next_cursor") or "").strip() or None
    has_more = bool(payload.get("has_more"))
    if has_more and not next_cursor:
        logger.warning("[Moltbook] continuation page omitted next_cursor: %s", url)
        return None
    return posts, next_cursor, has_more


def _scan_page(
    posts: list, known_links: set[str]
) -> tuple[list[dict], set[str], set[str]]:
    """Normalize one page and report moderated plus distinct usable links."""
    moderated: set[str] = set()
    usable_links: set[str] = set()
    for post in posts:
        if not isinstance(post, dict):
            continue
        link = _post_link(post)
        if link and (post.get("is_deleted") or post.get("is_spam")):
            moderated.add(link)
        if link and _usable_post(post):
            usable_links.add(link)
    return parse_posts({"posts": posts}, known_links), moderated, usable_links


def _append_unique(entries: list[dict], page_entries: list[dict], seen: set[str]) -> None:
    """Append page entries once even if an API page overlaps its neighbor."""
    for entry in page_entries:
        if entry["link"] in seen:
            continue
        seen.add(entry["link"])
        entries.append(entry)


def fetch_moltbook_pages(
    known_links: set[str], *, fetch=get_html
) -> tuple[list[dict], set[str], bool]:
    """Fetch the current Moltbook hot window used for publication.

    The API is ranked by ``sort=hot``. Pagination only continues when filtered
    or overlapping rows leave fewer than ``MOLTBOOK_HOT_WINDOW`` distinct
    usable posts. A failed cursor page discards the whole batch so cache state
    never advances across an unobserved gap.
    """
    entries: list[dict] = []
    moderated_links: set[str] = set()
    seen_entry_links: set[str] = set()
    usable_links_seen: set[str] = set()
    seen_cursors: set[str] = set()
    cursor: str | None = None

    while len(usable_links_seen) < MOLTBOOK_HOT_WINDOW:
        if cursor is not None:
            if cursor in seen_cursors:
                logger.warning("[Moltbook] repeated cursor detected: %s", cursor)
                return [], set(), False
            seen_cursors.add(cursor)

        loaded = _load_page(cursor, fetch)
        if loaded is None:
            return [], set(), False
        posts, next_cursor, has_more = loaded
        if not posts:
            if has_more:
                logger.warning("[Moltbook] empty page advertised a continuation")
                return [], set(), False
            break

        page_entries, page_moderated, page_usable_links = _scan_page(posts, known_links)
        _append_unique(entries, page_entries, seen_entry_links)
        moderated_links.update(page_moderated)
        usable_links_seen.update(page_usable_links)
        usable_links_seen.difference_update(moderated_links)
        if not has_more:
            break
        if next_cursor in seen_cursors:
            logger.warning("[Moltbook] cursor cycle detected: %s", next_cursor)
            return [], set(), False
        cursor = next_cursor

    logger.info(
        "[Moltbook] scanned %d distinct hot post(s), collected %d new, found %d moderated",
        len(usable_links_seen),
        len(entries),
        len(moderated_links & known_links),
    )
    return entries, moderated_links, True


def _fresh_unmoderated(
    entries: list[dict], known_links: set[str], moderated_links: set[str]
) -> list[dict]:
    """Exclude cached or newly moderated posts from a prefetched batch."""
    return [
        entry
        for entry in entries
        if entry["link"] not in known_links and entry["link"] not in moderated_links
    ]


def main(full: bool = False) -> bool:
    """Generate the combined Molt Atom feed."""
    fresh_entries, moderated_links, complete = fetch_moltbook_pages(set())
    if not complete:
        logger.warning("[Moltbook] incomplete pagination; preserving last good feed")
        return False
    current_hot_links = {entry["link"] for entry in fresh_entries}

    def scrape_prefetched(known_links: set[str]) -> list[dict]:
        """Return prefetched Moltbook entries that remain fresh and unmoderated."""
        return _fresh_unmoderated(fresh_entries, known_links, moderated_links)

    def keep_cached(entry: dict) -> bool:
        """Keep SpaceMolt history, but only Moltbook posts still in the hot window."""
        if entry.get("source") != SOURCE_NAME:
            return True
        link = entry.get("link")
        return link in current_hot_links and link not in moderated_links

    return run(
        feed_name=FEED_NAME,
        title="Molt",
        subtitle=(
            "Moltbook hot posts plus official SpaceMolt news and changelog updates, "
            "fair-shared across communities and official streams."
        ),
        blog_url=SITE_URL,
        author="Molt ecosystem",
        sources=SPACEMOLT_NATIVE_SOURCES,
        extra_scrapers=(scrape_spacemolt_changelog, scrape_prefetched),
        max_entries=MAX_ENTRIES,
        per_source_cap=PER_STREAM_CAP,
        allocation_field=ALLOCATION_FIELD,
        candidate_limit=CANDIDATE_LIMIT,
        candidate_source_reserve=CANDIDATE_SOURCE_RESERVE,
        image_backfill=False,
        cache_filter=keep_cached,
        cache_transform=_restore_submolt,
        dedupe_title_field=None,
        full=full,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate the combined Molt Atom feed")
    parser.add_argument(
        "--full", action="store_true", help="Ignore cache and rebuild from scratch"
    )
    sys.exit(0 if main(full=parser.parse_args().full) else 1)
