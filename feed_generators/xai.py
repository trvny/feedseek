from datetime import UTC

"""xAI feed generator.

Aggregates xAI's update sources into one **Atom** feed written to
``feeds/feed_xai.xml``:

    - xAI News               https://x.ai/news                          (HTML)
    - xAI Console changelog  https://x.ai/api/changelog                 (HTML)
    - Grok Build changelog   https://x.ai/build/changelog               (HTML)
    - xAI API release notes  https://docs.x.ai/developers/release-notes (Mintlify .md)
    - Grok release notes     https://grok.com/release-notes             (HTML)
    - X Blog                 https://blog.x.com/                         (HTML)
    - X Engineering          https://blog.x.com/engineering/en_us        (HTML)
    - X API changelog        https://docs.x.com/changelog                (HTML)

Source handling:
  * News — server-rendered listing cards: ``<a href="/news/...">`` with an
    ``<h1-3>`` title and a "Jun 3, 2026" date node inside the card; a card
    with no heading falls back to a slug-derived title. x.ai 403s plain
    requests, so fetches go through curl_cffi Chrome impersonation.
  * Grok Build changelog — each release is an ``<h2 id="v<ver>-<YYYY-MM-DD>">``,
    so the anchor carries both a stable fragment and the date. The body is the
    text up to the next ``<h2>``.
  * API release notes — fetched as Mintlify raw markdown (``<path>.md``),
    organized as ``## <Month>`` (no year, newest first) containing ``###``
    feature sections. The year is inferred by rolling back whenever the month
    jumps upward while walking down; entries are dated to the 1st of their
    month and linked by the Mintlify heading anchor (fragments are the only
    differentiator between entries — preserve them).

History accumulates across runs via the shared JSON cache
(``cache/xai_posts.json``); entries dedupe by link, then cross-source by
normalized URL/title.
"""

import argparse
import re
import sys
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from enrich import enrich_entries
from entry_identity import entry_id_for
from feedgen.feed import FeedGenerator
from utils import (
    add_entry_media,
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
    stable_fallback_date,
)
from x_changelog import BLOG_URL as X_API_CHANGELOG_URL
from x_changelog import fetch_text as fetch_x_api_changelog
from x_changelog import parse_items as parse_x_api_items

logger = setup_logging()

FEED_NAME = "xai"
BLOG_URL = "https://x.ai/news"

NEWS_URL = "https://x.ai/news"
NEWS_BASE = "https://x.ai"
CONSOLE_CHANGELOG_URL = "https://x.ai/api/changelog"
BUILD_CHANGELOG_URL = "https://x.ai/build/changelog"
RELEASE_NOTES_URL = "https://docs.x.ai/developers/release-notes"
RELEASE_NOTES_MD_URL = "https://docs.x.ai/developers/release-notes.md"
GROK_RELEASE_NOTES_URL = "https://grok.com/release-notes"
X_BLOG_URL = "https://blog.x.com/"
X_ENGINEERING_URL = "https://blog.x.com/engineering/en_us"

DATE_RE = re.compile(
    r"((?:January|February|March|April|May|June|July|August|September|October|November|December"
    r"|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\.?\s+\d{1,2},?\s+\d{4})"
)
MONTH_NAMES = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
}
# Grok Build h2 anchors look like "v0.2.20-2026-06-03".
_BUILD_ID_RE = re.compile(r"^v.+-(\d{4}-\d{2}-\d{2})$")
_CONSOLE_DATE_RE = re.compile(
    r"^(?:January|February|March|April|May|June|July|August|September|October|"
    r"November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)"
    r"\.?\s+\d{1,2},?\s+\d{4}$"
)
_X_BLOG_DATE_RE = re.compile(
    r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+"
    r"(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|"
    r"September|October|November|December)\s+\d{4})",
    re.IGNORECASE,
)
_GROK_RELEASE_RE = re.compile(
    r"/release-notes/([a-z]{3})-(\d{1,2})-(\d{4})(?:[/?#\"']|$)",
    re.IGNORECASE,
)

DESC_LIMIT = 500
MAX_ENTRIES = 200
X_API_MAX_ENTRIES = 50


def _get_html(url):
    """Fetch a URL impersonating Chrome (x.ai 403s plain clients);
    fall back to plain requests if curl_cffi is unavailable. Returns text or None."""
    try:
        from curl_cffi import requests as creq

        resp = creq.get(url, impersonate="chrome", timeout=30)
    except ImportError:
        logger.warning(f"curl_cffi unavailable; using plain requests for {url}")
        try:
            resp = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0"},
                timeout=30,
            )
        except Exception as e:
            logger.warning(f"Fetch failed for {url}: {e}")
            return None
    except Exception as e:
        logger.warning(f"Fetch failed for {url}: {e}")
        return None
    if resp.status_code != 200:
        logger.warning(f"Fetch for {url} returned HTTP {resp.status_code}")
        return None
    return resp.text


def parse_date(date_str):
    """Parse a date string into a UTC datetime, or None on failure."""
    try:
        dt = date_parser.parse(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)
    except (ValueError, TypeError, OverflowError) as e:
        logger.warning(f"Could not parse date '{date_str}': {e}")
        return None


def slugify(text):
    """Mintlify/GitHub-style heading anchor: lowercase, non-alnum -> hyphen."""
    return re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")


def title_from_slug(href):
    slug = href.rstrip("/").split("/")[-1]
    return slug.replace("-", " ").replace("_", " ").strip().capitalize()


def clean_markdown(text, limit=DESC_LIMIT):
    """Reduce markdown to readable plain text for a feed summary."""
    text = re.sub(r"<[^>]+>", " ", text)                    # JSX/HTML components
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)        # images
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)     # links -> link text
    text = re.sub(r"[`*_>#]", " ", text)                     # md punctuation
    text = re.sub(r"^\s*[-+]\s+", "", text, flags=re.MULTILINE)  # bullets
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


# --------------------------------------------------------------------------- #
# xAI News (server-rendered listing cards)
# --------------------------------------------------------------------------- #


def scrape_news(known_links):
    label = "xAI News"
    entries = []
    html = _get_html(NEWS_URL)
    if html is None:
        return entries
    soup = BeautifulSoup(html, "html.parser")

    seen = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not href.startswith("/news/") or href == "/news/" or href in seen:
            continue
        seen.add(href)
        link = NEWS_BASE + href
        if link in known_links:
            continue
        try:
            heading = a.find(["h1", "h2", "h3"])
            title = heading.get_text(" ", strip=True) if heading else title_from_slug(href)
            m = DATE_RE.search(a.get_text(" ", strip=True))
            date_obj = parse_date(m.group(1)) if m else stable_fallback_date(link)
            entries.append({
                "title": sanitize_xml(title),
                "link": link,
                "date": date_obj,
                "description": sanitize_xml(title),
                "source": label,
            })
            logger.info(f"  [{label}] {title}")
        except Exception as e:
            logger.warning(f"  [{label}] skipping malformed card {href}: {e}")
    return entries


# --------------------------------------------------------------------------- #
# xAI Console changelog (date block -> heading + bullets)
# --------------------------------------------------------------------------- #


def _parse_console_changelog(html):
    soup = BeautifulSoup(html, "html.parser")
    entries = []
    seen_links = set()

    date_nodes = []
    for text_node in soup.find_all(string=True):
        text = re.sub(r"\s+", " ", str(text_node)).strip()
        if _CONSOLE_DATE_RE.fullmatch(text):
            date_nodes.append((text_node, text))

    for text_node, date_text in date_nodes:
        date_obj = parse_date(date_text)
        if date_obj is None:
            continue

        title = None
        parts = []
        seen_parts = set()

        for node in text_node.parent.next_elements:
            if node is text_node:
                continue

            if isinstance(node, str):
                next_text = re.sub(r"\s+", " ", str(node)).strip()
                if _CONSOLE_DATE_RE.fullmatch(next_text):
                    break
                continue

            name = getattr(node, "name", None)
            if name in {"h2", "h3"} and title is None:
                heading_text = re.sub(r"\s+", " ", node.get_text(" ", strip=True))
                if heading_text and heading_text != "Changelog":
                    title = heading_text
                continue

            if name not in {"p", "li"}:
                continue
            body_text = re.sub(r"\s+", " ", node.get_text(" ", strip=True))
            if (
                not body_text
                or body_text == title
                or _CONSOLE_DATE_RE.fullmatch(body_text)
                or body_text in seen_parts
            ):
                continue
            seen_parts.add(body_text)
            parts.append(body_text)

        title = sanitize_xml(title or f"SpaceXAI Console update — {date_text}")
        fragment = (
            f"console-{date_obj.date().isoformat()}-"
            f"{slugify(title)[:48]}"
        )
        link = f"{CONSOLE_CHANGELOG_URL}#{fragment}"
        if link in seen_links:
            continue

        description = sanitize_xml(" ".join(parts))[:DESC_LIMIT] or title
        entries.append({
            "title": title,
            "link": link,
            "date": date_obj,
            "description": description,
            "source": "xAI Console changelog",
        })
        seen_links.add(link)

    return entries


def scrape_console_changelog(known_links):
    html = _get_html(CONSOLE_CHANGELOG_URL)
    if html is None:
        return []
    candidates = _parse_console_changelog(html)
    entries = [entry for entry in candidates if entry["link"] not in known_links]
    if not candidates:
        logger.warning("  [xAI Console changelog] no updates matched — layout may have changed")
    for entry in entries:
        logger.info(f"  [xAI Console changelog] {entry['title']}")
    return entries


# --------------------------------------------------------------------------- #
# Grok Build changelog (h2 id="v<version>-<date>")
# --------------------------------------------------------------------------- #


def scrape_build_changelog(known_links):
    label = "Grok Build changelog"
    entries = []
    html = _get_html(BUILD_CHANGELOG_URL)
    if html is None:
        return entries
    soup = BeautifulSoup(html, "html.parser")

    headings = soup.find_all("h2", id=_BUILD_ID_RE)
    if not headings:
        logger.warning(f"  [{label}] no release headings matched — layout may have changed")
        return entries

    for h in headings:
        try:
            anchor = h.get("id")
            link = f"{BUILD_CHANGELOG_URL}#{anchor}"
            if link in known_links:
                continue
            date_obj = parse_date(_BUILD_ID_RE.match(anchor).group(1))
            title = sanitize_xml(h.get_text(" ", strip=True))
            parts = []
            for el in h.next_elements:
                if getattr(el, "name", None) == "h2" and el is not h:
                    break
                if getattr(el, "name", None) in ("p", "li"):
                    parts.append(el.get_text(" ", strip=True))
            desc = re.sub(r"\s+", " ", " ".join(parts)).strip()[:DESC_LIMIT]
            entries.append({
                "title": title,
                "link": link,
                "date": date_obj,
                "description": sanitize_xml(desc) or title,
                "source": label,
            })
            logger.info(f"  [{label}] {title}")
        except Exception as e:
            logger.warning(f"  [{label}] skipping malformed item: {e}")
    return entries


# --------------------------------------------------------------------------- #
# xAI API release notes (Mintlify markdown: ## Month / ### feature)
# --------------------------------------------------------------------------- #


def scrape_release_notes(known_links, today=None):
    import datetime as _dt

    label = "xAI API release notes"
    entries = []
    md = _get_html(RELEASE_NOTES_MD_URL)
    if md is None:
        return entries

    # Walk the markdown line by line: "## <Month>" sets the current month
    # (year inferred newest-first, rolling back when the month jumps upward),
    # "### <heading>" starts a feature section.
    today = today or _dt.datetime.now(UTC)
    year, prev_month = today.year, None
    cur_date = None
    sections = []   # (heading, date, [body lines])

    for line in md.splitlines():
        m2 = re.match(r"^##\s+([A-Za-z]+)\s*$", line)
        if m2 and m2.group(1).lower() in MONTH_NAMES:
            month = MONTH_NAMES[m2.group(1).lower()]
            if prev_month is None:
                if month > today.month:
                    year -= 1
            elif month > prev_month:
                year -= 1
            prev_month = month
            cur_date = _dt.datetime(year, month, 1, tzinfo=UTC)
            continue
        m3 = re.match(r"^###\s+(.+?)\s*$", line)
        if m3 and cur_date is not None:
            sections.append([m3.group(1), cur_date, []])
            continue
        if sections and cur_date is not None:
            sections[-1][2].append(line)

    if not sections:
        logger.warning(f"  [{label}] no sections parsed — page structure may have changed")
        return entries

    seen_slugs = {}
    for heading, date_obj, body in sections:
        try:
            slug = slugify(heading)
            # Mintlify suffixes repeated heading anchors with -2, -3, ...
            seen_slugs[slug] = seen_slugs.get(slug, 0) + 1
            if seen_slugs[slug] > 1:
                slug = f"{slug}-{seen_slugs[slug]}"
            link = f"{RELEASE_NOTES_URL}#{slug}"
            if link in known_links:
                continue
            desc = clean_markdown("\n".join(body)) or heading
            entries.append({
                "title": sanitize_xml(heading),
                "link": link,
                "date": date_obj,
                "description": sanitize_xml(desc),
                "source": label,
            })
            logger.info(f"  [{label}] {heading}")
        except Exception as e:
            logger.warning(f"  [{label}] skipping malformed section: {e}")
    return entries


# --------------------------------------------------------------------------- #
# X Blog / Engineering
# --------------------------------------------------------------------------- #


def _ancestor_with_date(anchor, date_re):
    """Return the nearest ancestor whose text contains a matching date."""
    for parent in [anchor, *anchor.parents]:
        if getattr(parent, "name", None) == "main":
            break
        text = re.sub(r"\s+", " ", parent.get_text(" ", strip=True))
        match = date_re.search(text)
        if match:
            return parent, match
    return anchor, None


def _parse_x_blog_index(html, label, page_url, path_prefix):
    soup = BeautifulSoup(html, "html.parser")
    entries = []
    seen_links = set()

    for anchor in soup.find_all("a", href=True):
        link = urljoin(page_url, anchor.get("href", ""))
        parsed = urlparse(link)
        if parsed.netloc != "blog.x.com" or not parsed.path.startswith(path_prefix):
            continue
        if link in seen_links:
            continue

        title = re.sub(r"\s+", " ", anchor.get_text(" ", strip=True))
        if not title or title.lower() in {"see more", "back"}:
            continue

        card, match = _ancestor_with_date(anchor, _X_BLOG_DATE_RE)
        if match is None:
            continue
        date_obj = parse_date(match.group(1))
        if date_obj is None:
            continue

        description = title
        paragraph = card.find("p") if hasattr(card, "find") else None
        if paragraph:
            paragraph_text = re.sub(r"\s+", " ", paragraph.get_text(" ", strip=True))
            if paragraph_text and paragraph_text != title:
                description = paragraph_text[:DESC_LIMIT]

        entries.append({
            "title": sanitize_xml(title),
            "link": link,
            "date": date_obj,
            "description": sanitize_xml(description),
            "source": label,
        })
        seen_links.add(link)

    return entries


def scrape_x_blog(label, page_url, path_prefix, known_links):
    html = _get_html(page_url)
    if html is None:
        return []
    candidates = _parse_x_blog_index(html, label, page_url, path_prefix)
    entries = [entry for entry in candidates if entry["link"] not in known_links]
    if not candidates:
        logger.warning(f"  [{label}] no posts matched — layout may have changed")
    for entry in entries:
        logger.info(f"  [{label}] {entry['title']}")
    return entries


# --------------------------------------------------------------------------- #
# Grok release notes
# --------------------------------------------------------------------------- #


def _parse_grok_release_notes_index(html):
    import datetime as _dt

    matches = {}
    soup = BeautifulSoup(html, "html.parser")

    for anchor in soup.find_all("a", href=True):
        link = urljoin(GROK_RELEASE_NOTES_URL, anchor.get("href", ""))
        match = _GROK_RELEASE_RE.search(urlparse(link).path + "/")
        if not match:
            continue
        matches[link.rstrip("/")] = re.sub(
            r"\s+", " ", anchor.get_text(" ", strip=True)
        )

    # grok.com may serialize client-side links into its app payload rather than
    # server-rendering anchors. Extract those paths too, but keep the same
    # canonical URL/date logic.
    serialized_html = html.replace("\\/", "/")
    for match in _GROK_RELEASE_RE.finditer(serialized_html):
        path = match.group(0).rstrip("/?#\"'")
        path = re.sub(r"[\\\"]+$", "", path)
        link = urljoin(GROK_RELEASE_NOTES_URL, path).rstrip("/")
        matches.setdefault(link, "")

    entries = []
    month_numbers = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    }
    for link, anchor_text in matches.items():
        match = _GROK_RELEASE_RE.search(urlparse(link).path + "/")
        if not match:
            continue
        month = month_numbers.get(match.group(1).lower())
        if month is None:
            continue
        date_obj = _dt.datetime(
            int(match.group(3)), month, int(match.group(2)), tzinfo=UTC
        )
        date_label = date_obj.strftime("%b %d, %Y")
        anchor_is_date = parse_date(anchor_text) is not None if anchor_text else False
        title = (
            f"Grok release notes — {date_label}"
            if not anchor_text or anchor_is_date
            else anchor_text
        )
        entries.append({
            "title": sanitize_xml(title),
            "link": link,
            "date": date_obj,
            "description": sanitize_xml(title),
            "source": "Grok release notes",
        })

    return sorted(entries, key=lambda entry: entry["date"], reverse=True)


def scrape_grok_release_notes(known_links):
    html = _get_html(GROK_RELEASE_NOTES_URL)
    if html is None:
        return []
    candidates = _parse_grok_release_notes_index(html)
    entries = [entry for entry in candidates if entry["link"] not in known_links]
    if not candidates:
        logger.warning("  [Grok release notes] no releases matched — layout may have changed")
    for entry in entries:
        logger.info(f"  [Grok release notes] {entry['title']}")
    return entries


# --------------------------------------------------------------------------- #
# X (Twitter) API changelog
# --------------------------------------------------------------------------- #


def scrape_x_api_changelog(known_links):
    label = "X API changelog"
    html = fetch_x_api_changelog(X_API_CHANGELOG_URL)
    if html is None:
        logger.warning(f"  [{label}] fetch failed")
        return []

    entries = []
    items = sort_posts_for_feed(parse_x_api_items(html), date_field="date")
    for item in items[-X_API_MAX_ENTRIES:]:
        if item["link"] in known_links:
            continue
        item["source"] = label
        entries.append(item)
        logger.info(f"  [{label}] {item['title']}")
    return entries


def _cap_x_api_history(entries):
    """Keep only the newest X API changelog slice in the aggregate cache."""
    x_api = [entry for entry in entries if entry.get("source") == "X API changelog"]
    if len(x_api) <= X_API_MAX_ENTRIES:
        return entries
    x_api = sort_posts_for_feed(x_api, date_field="date")[-X_API_MAX_ENTRIES:]
    keep = {entry["link"] for entry in x_api}
    return [
        entry
        for entry in entries
        if entry.get("source") != "X API changelog" or entry["link"] in keep
    ]


def _seed_legacy_x_api_cache(cached):
    """Migrate the old standalone X API cache on the first grouped run."""
    if any(entry.get("source") == "X API changelog" for entry in cached):
        return cached

    legacy = deserialize_entries(
        load_cache("x_changelog").get("entries", []), date_field="date"
    )
    if not legacy:
        return cached

    for entry in legacy:
        entry["source"] = "X API changelog"
    logger.info("Migrating %d entries from the legacy X API cache", len(legacy))
    merged = merge_entries(legacy, cached, id_field="link", date_field="date")
    return _cap_x_api_history(merged)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #


def scrape_all(known_links):
    new_entries = []
    logger.info("Scraping xAI News ...")
    new_entries += scrape_news(known_links)
    logger.info("Scraping xAI Console changelog ...")
    new_entries += scrape_console_changelog(known_links)
    logger.info("Scraping Grok Build changelog ...")
    new_entries += scrape_build_changelog(known_links)
    logger.info("Scraping xAI API release notes ...")
    new_entries += scrape_release_notes(known_links)
    logger.info("Scraping Grok release notes ...")
    new_entries += scrape_grok_release_notes(known_links)
    logger.info("Scraping X Blog ...")
    new_entries += scrape_x_blog("X Blog", X_BLOG_URL, "/en_us/topics/", known_links)
    logger.info("Scraping X Engineering ...")
    new_entries += scrape_x_blog(
        "X Engineering", X_ENGINEERING_URL, "/engineering/en_us/", known_links
    )
    logger.info("Scraping X API changelog ...")
    new_entries += scrape_x_api_changelog(known_links)
    return new_entries


def generate_atom_feed(articles, feed_name=FEED_NAME):
    fg = FeedGenerator()
    fg.id(f"https://x.ai/{feed_name}")
    fg.title("xAI")
    fg.subtitle(
        "xAI and Grok product updates, Console and Build changelogs, plus "
        "X Blog, X Engineering, and the X developer API changelog."
    )
    setup_feed_links(fg, BLOG_URL, feed_name)
    setup_feed_extensions(fg)
    fg.language("en")
    fg.author({"name": "xAI"})

    for article in articles:
        fe = fg.add_entry()
        fe.id(entry_id_for(FEED_NAME, article))
        fe.title(article["title"])
        fe.link(href=article["link"])
        source = article.get("source")
        if source:
            fe.category(term=source, label=source)
        fe.description(article.get("description") or article["title"])
        add_entry_media(
            fe,
            article.get("image"),
            width=article.get("image_width"),
            height=article.get("image_height"),
        )
        if article.get("date"):
            fe.published(article["date"])
            fe.updated(article["date"])

    logger.info("Generated Atom feed")
    return fg


def main(full=False):
    if full:
        logger.info("Full reset requested — ignoring existing cache")
        cached = []
    else:
        cache = load_cache(FEED_NAME)
        cached = deserialize_entries(cache.get("entries", []), date_field="date")
        cached = _seed_legacy_x_api_cache(cached)

    known_links = {e["link"] for e in cached}
    new_articles = scrape_all(known_links)

    if not new_articles and not cached:
        logger.warning("No articles collected — skipping write to avoid an empty feed")
        return False

    merged = merge_entries(new_articles, cached, id_field="link", date_field="date")
    merged = dedupe_entries(merged, id_field="link", title_field="title", date_field="date")
    merged = _cap_x_api_history(merged)
    merged = sort_posts_for_feed(merged, date_field="date")

    # Keep full (deduplicated) history in the cache so already-seen links are
    # never re-evaluated on later runs; only the rendered feed is capped.
    feed_items = merged[-MAX_ENTRIES:] if len(merged) > MAX_ENTRIES else merged
    # Before the cache write: feed_items shares its dicts with merged, so a
    # resolved image is saved and never looked up again.
    enrich_entries(feed_items)
    save_cache(FEED_NAME, merged)

    fg = generate_atom_feed(feed_items)
    save_atom_feed(fg, FEED_NAME)
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate the xAI Atom feed")
    parser.add_argument("--full", action="store_true", help="Ignore cache and rebuild from scratch")
    args = parser.parse_args()
    sys.exit(0 if main(full=args.full) else 1)
