"""Newsify Today feed generator.

Combines the Poland editions requested for Feedseek into one Atom feed:

- Polish:  https://newsify.today/polish/PL
- English: https://newsify.today/english/PL

Newsify does not expose a discoverable native RSS/Atom feed for these pages, so
this generator parses their server-rendered article cards. Each language stays
separately attributed while both share one cache and one published feed.
"""

import argparse
import re
import sys
from datetime import datetime
from urllib.parse import quote, unquote, urljoin, urlsplit, urlunsplit
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
from enrich import enrich_entries
from entry_identity import entry_id_for
from feedgen.feed import FeedGenerator
from utils import (
    add_entry_media,
    allocate_fair_share,
    dedupe_entries,
    deserialize_entries,
    fetch_page,
    load_cache,
    localize_wall_time,
    merge_entries,
    sanitize_xml,
    save_atom_feed,
    save_cache,
    set_entry_source,
    setup_feed_extensions,
    setup_feed_links,
    setup_logging,
    sort_posts_for_feed,
)

logger = setup_logging()

FEED_NAME = "newsify"
BLOG_URL = "https://newsify.today/polish/PL"
MAX_ENTRIES = 200

SOURCES = [
    ("Newsify Polski", "https://newsify.today/polish/PL", "polish", "pl"),
    ("Newsify English", "https://newsify.today/english/PL", "english", "en"),
]

WARSAW = ZoneInfo("Europe/Warsaw")
DATE_RE = re.compile(r"\b(\d{2}\.\d{2}\.\d{4}),\s*(\d{2}:\d{2})\b")
TREND_RE = re.compile(
    r"\bTrend:\s*(.+?)(?=\s*(?:Read more|Czytaj więcej)\b|$)", re.IGNORECASE
)
SKIP_LINK_TEXT = {"read more", "czytaj więcej", "more", "więcej"}
CARD_HINT_RE = re.compile(
    r"(^|[-_])(article|card|item|news|post|story)([-_]|$)", re.IGNORECASE
)


def _clean(text):
    """Collapse display whitespace used by Newsify cards."""
    return re.sub(r"\s+", " ", text or "").strip()


def parse_date(text):
    """Parse Newsify's Poland-local DD.MM.YYYY, HH:MM timestamp to UTC."""
    match = DATE_RE.search(text or "")
    if not match:
        return None
    try:
        naive = datetime.strptime(
            f"{match.group(1)}, {match.group(2)}", "%d.%m.%Y, %H:%M"
        )
        return localize_wall_time(naive, WARSAW).astimezone(ZoneInfo("UTC"))
    except ValueError:
        return None


def _decode_repeated(value):
    """Decode repeatedly escaped path text to one stable Unicode value."""
    for _ in range(32):
        decoded = unquote(value)
        if decoded == value:
            break
        value = decoded
    return value


def _normalize_path(path):
    """Normalize every URL path segment and percent-encode it exactly once."""
    safe = "-._~!$&'()*+,;=:@"
    return "/".join(
        quote(_decode_repeated(segment), safe=safe) for segment in path.split("/")
    )


def _canonical_article_url(base_url, href):
    """Return a canonical Newsify article URL, rejecting lookalike hosts."""
    link = urljoin(base_url, href)
    parts = urlsplit(link)
    if (parts.hostname or "").lower() != "newsify.today":
        return None
    return urlunsplit(
        (parts.scheme or "https", "newsify.today", _normalize_path(parts.path), "", "")
    )


def _has_card_hint(node):
    """Return whether an ancestor looks like a single semantic article card."""
    if getattr(node, "name", None) in {"article", "li"}:
        return True
    tokens = [node.get("id", ""), *node.get("class", [])]
    return any(CARD_HINT_RE.search(str(token)) for token in tokens if token)


def _article_link_count(node):
    """Count unique descendant article hrefs without relying on layout classes."""
    if not hasattr(node, "find_all"):
        return 0
    return len(
        {
            anchor.get("href")
            for anchor in node.find_all("a", href=True)
            if "/article/" in anchor.get("href", "")
        }
    )


def _article_card(anchor):
    """Find one article boundary without borrowing metadata from a sibling."""
    fallback = anchor.parent or anchor
    for parent in anchor.parents:
        name = getattr(parent, "name", None)
        if name in {"main", "body", "html"}:
            break
        if _has_card_hint(parent):
            return parent

        article_count = _article_link_count(parent)
        if article_count > 1:
            return fallback

        fallback = parent
        if DATE_RE.search(_clean(parent.get_text(" ", strip=True))):
            return parent
    return fallback


def _title_from_slug(link):
    """Build a readable fallback title from an article URL slug."""
    slug = urlsplit(link).path.rstrip("/").split("/")[-1]
    slug = _decode_repeated(slug)
    return _clean(slug.replace("-", " ").replace("_", " ")).capitalize()


def _extract_title(card, anchor, link):
    """Prefer the card heading, then useful anchor text, then the URL slug."""
    heading = card.find(["h1", "h2", "h3", "h4"]) if hasattr(card, "find") else None
    if heading:
        title = _clean(heading.get_text(" ", strip=True))
        if title:
            return title

    anchor_text = _clean(anchor.get_text(" ", strip=True))
    if anchor_text and anchor_text.lower() not in SKIP_LINK_TEXT:
        return anchor_text
    return _title_from_slug(link)


def _extract_description(card, title):
    """Choose the most informative paragraph from one article card."""
    if not hasattr(card, "find_all"):
        return title

    candidates = []
    for node in card.find_all("p"):
        text = _clean(node.get_text(" ", strip=True))
        if (
            not text
            or text == title
            or DATE_RE.fullmatch(text)
            or text.lower() in SKIP_LINK_TEXT
            or text.lower().startswith("trend:")
        ):
            continue
        candidates.append(text)

    return max(candidates, key=len)[:1000] if candidates else title


def _extract_trend(card):
    """Extract Newsify's optional Trend label from a card."""
    if not hasattr(card, "get_text"):
        return None
    match = TREND_RE.search(_clean(card.get_text(" ", strip=True)))
    return sanitize_xml(_clean(match.group(1))) if match else None


def _extract_image(card, page_url):
    """Resolve the first usable card image against the listing URL."""
    if not hasattr(card, "find"):
        return None
    image = card.find("img")
    if not image:
        return None
    src = image.get("src") or image.get("data-src") or image.get("data-lazy-src")
    if not src or src.startswith("data:"):
        return None
    return urljoin(page_url, src)


def parse_listing(html, label, page_url, language_path, language_code):
    """Parse one Newsify listing page into normalized Feedseek entries."""
    soup = BeautifulSoup(html, "html.parser")
    prefix = f"/{language_path}/PL/article/"
    entries = []
    seen_links = set()

    for anchor in soup.find_all("a", href=True):
        link = _canonical_article_url(page_url, anchor.get("href", ""))
        if not link or not urlsplit(link).path.startswith(prefix) or link in seen_links:
            continue

        card = _article_card(anchor)
        card_text = _clean(card.get_text(" ", strip=True))
        title = sanitize_xml(_extract_title(card, anchor, link))
        if not title:
            continue

        entries.append(
            {
                "title": title,
                "link": link,
                "date": parse_date(card_text),
                "description": sanitize_xml(_extract_description(card, title)),
                "source": label,
                "language": language_code,
                "trend": _extract_trend(card),
                "image": _extract_image(card, page_url),
            }
        )
        seen_links.add(link)

    return entries


def scrape_source(label, page_url, language_path, language_code, known_links):
    """Fetch and parse one Newsify language edition without blocking the other."""
    try:
        html = fetch_page(page_url)
    except Exception as exc:
        logger.warning("[%s] fetch failed: %s", label, exc)
        return []

    candidates = parse_listing(html, label, page_url, language_path, language_code)
    if not candidates:
        logger.warning("[%s] no article cards matched — layout may have changed", label)
        return []

    entries = [entry for entry in candidates if entry["link"] not in known_links]
    for entry in entries:
        logger.info("  [%s] %s", label, entry["title"])
    return entries


def scrape_all(known_links):
    """Collect unseen entries from both requested Poland editions."""
    entries = []
    for label, page_url, language_path, language_code in SOURCES:
        logger.info("Scraping %s ...", label)
        entries.extend(
            scrape_source(label, page_url, language_path, language_code, known_links)
        )
    return entries


def generate_atom_feed(articles, feed_name=FEED_NAME):
    """Render normalized Newsify entries as the published Atom feed."""
    fg = FeedGenerator()
    fg.id("https://newsify.today/")
    fg.title("Newsify")
    fg.subtitle("Newsify Today for Poland — Polish and English editions.")
    setup_feed_links(fg, BLOG_URL, feed_name)
    setup_feed_extensions(fg)
    fg.language("mul")
    fg.author({"name": "Newsify Today"})

    for article in articles:
        fe = fg.add_entry()
        fe.id(entry_id_for(feed_name, article))
        fe.title(article["title"])
        fe.link(href=article["link"])
        fe.description(article.get("description") or article["title"])
        set_entry_source(fe, article.get("source"))

        language = article.get("language")
        if language:
            fe.category(term=language, label=f"Language: {language}")
        trend = article.get("trend")
        if trend:
            fe.category(term=trend, label=f"Trend: {trend}")

        add_entry_media(fe, article.get("image"))
        if article.get("date"):
            fe.published(article["date"])
            fe.updated(article["date"])

    return fg


def _dedupe_articles(entries):
    """Deduplicate only by canonical article URL; duplicate headlines are valid."""
    return dedupe_entries(entries, id_field="link", title_field=None, date_field="date")


def main(full=False):
    """Merge live Newsify entries with cache and publish the feed pair."""
    if full:
        logger.info("Full reset requested — ignoring existing cache")
        cached = []
    else:
        cache = load_cache(FEED_NAME)
        cached = deserialize_entries(cache.get("entries", []), date_field="date")

    known_links = {entry["link"] for entry in cached}
    new_entries = scrape_all(known_links)

    if not new_entries and not cached:
        logger.warning("No articles collected — skipping write to avoid an empty feed")
        return False

    merged = merge_entries(new_entries, cached, id_field="link", date_field="date")
    merged = _dedupe_articles(merged)
    merged = sort_posts_for_feed(merged, date_field="date")

    feed_items = allocate_fair_share(merged, MAX_ENTRIES, date_field="date")
    enrich_entries(feed_items)
    save_cache(FEED_NAME, merged)

    fg = generate_atom_feed(feed_items)
    save_atom_feed(fg, FEED_NAME)
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate the Newsify Atom feed")
    parser.add_argument(
        "--full", action="store_true", help="Ignore cache and rebuild from scratch"
    )
    args = parser.parse_args()
    sys.exit(0 if main(full=args.full) else 1)
