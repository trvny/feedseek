"""Figma aggregate: two native Atom feeds and the dated Newsroom cards.

The Newsroom largely republishes Figma Blog articles. Use shared URL-based
deduplication so a press announcement does not appear twice.
"""

import argparse
import re
import sys
from datetime import datetime, timezone
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup, Tag

import multi_rss

FEED_NAME = "figma"
NEWSROOM_URL = "https://www.figma.com/newsroom/?lang=pl-pl"
BLOG_FEED_URL = "https://www.figma.com/blog/feed/atom.xml"
RELEASE_FEED_URL = "https://www.figma.com/release-notes/feed/atom.xml"
SOURCES = [
    ("Figma Blog", BLOG_FEED_URL, 80),
    ("Figma Release Notes", RELEASE_FEED_URL, 80),
]

# English newsroom cards and Polish-language localization of the same listing.
_DATE_RE = re.compile(
    r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?"
    r"|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?"
    r"|Dec(?:ember)?)\s+\d{1,2},?\s+20\d{2}\b"
    r"|\b\d{1,2}\s+(?:stycznia|lutego|marca|kwietnia|maja|czerwca"
    r"|lipca|sierpnia|września|października|listopada|grudnia)\s+20\d{2}\b",
    re.IGNORECASE,
)
_NEWS_HEADING = re.compile(r"news from figma|wiadomości od figma", re.IGNORECASE)


def doc_sources():
    """Provide the Newsroom page alongside the directly consumed Atom URLs."""
    return [("Figma Newsroom", NEWSROOM_URL)]


def _article_link(anchor):
    """Only keep Figma editorial articles, never navigation or category pages."""
    url = urljoin(NEWSROOM_URL, anchor.get("href", ""))
    parsed = urlsplit(url)
    if parsed.hostname not in {"figma.com", "www.figma.com"}:
        return None
    path = parsed.path.rstrip("/")
    if not (path.startswith("/blog/") or path.startswith("/newsroom/")):
        return None
    if path in {"/blog/news", "/blog/everything", "/newsroom"}:
        return None
    # Locale parameters change the view, not the identity of an article.
    query = urlencode(
        [(key, value) for key, value in parse_qsl(parsed.query) if key.lower() != "lang"]
    )
    return multi_rss.normalize_link(
        urlunsplit((parsed.scheme, parsed.netloc, parsed.path, query, ""))
    )


def _card_entry(heading):
    """Extract one complete card, avoiding dates from neighboring cards."""
    # BeautifulSoup excludes the heading itself from find_all("h3").
    for card in list(heading.parents)[:6]:
        if card.name in {"main", "body", "html"}:
            break
        if len(card.find_all("h3")) != 1:
            break

        anchors = ([card] if card.name == "a" and card.get("href") else [])
        anchors += card.find_all("a", href=True)
        link = next((value for a in anchors if (value := _article_link(a))), None)
        if not link:
            continue

        time_tag = card.find("time", datetime=True)
        raw_date = time_tag.get("datetime") if time_tag else None
        if not raw_date:
            match = _DATE_RE.search(card.get_text(" ", strip=True))
            raw_date = match.group() if match else None
        if not raw_date:
            continue
        date = multi_rss.parse_date(raw_date)
        if not date or date.date() > datetime.now(timezone.utc).date():
            return None

        title = multi_rss.sanitize_xml(heading.get_text(" ", strip=True))
        if not title:
            return None
        summary_el = card.find("p")
        description = (
            multi_rss.sanitize_xml(summary_el.get_text(" ", strip=True))
            if summary_el else title
        )
        return {
            "title": title,
            "link": link,
            "date": date,
            "description": description or title,
            "source": "Figma Newsroom",
        }
    return None


def parse_newsroom(html, known_links):
    """Read only dated article cards under the Newsroom's news section."""
    soup = BeautifulSoup(html, "html.parser")
    section = next(
        (
            h for h in soup.find_all("h2")
            if _NEWS_HEADING.search(h.get_text(" ", strip=True))
        ),
        None,
    )
    if section is None:
        multi_rss.logger.warning("Figma Newsroom news section not found")
        return []

    seen = {multi_rss.normalize_link(link) for link in known_links}
    entries = []
    for node in section.next_elements:
        if not isinstance(node, Tag):
            continue
        if node.name == "h2":
            break
        if node.name != "h3":
            continue
        entry = _card_entry(node)
        if entry is not None and entry["link"] not in seen:
            entries.append(entry)
            seen.add(entry["link"])
    if not entries:
        multi_rss.logger.info("Figma Newsroom yielded no unseen article cards")
    return entries


def scrape_newsroom(known_links):
    html = multi_rss.get_html(NEWSROOM_URL)
    if not html:
        return []
    return parse_newsroom(html, known_links)


def promote_cached_newsroom(entry):
    """Allow native Blog metadata to correct an earlier Newsroom fallback.

    The Blog is authoritative for articles at /blog/; keep the cached link
    and stable entry ID when upgrading the source label.
    """
    if entry.get("source") != "Figma Newsroom":
        return entry
    link = entry.get("link") or ""
    parsed = urlsplit(multi_rss.normalize_link(link))
    if parsed.hostname != "figma.com" or not parsed.path.startswith("/blog/"):
        return entry
    updated = dict(entry)
    updated["source"] = "Figma Blog"
    return updated


def main(full=False):
    return multi_rss.run(
        feed_name=FEED_NAME,
        title="Figma",
        subtitle="Figma Newsroom, blog and product release notes.",
        blog_url=NEWSROOM_URL,
        author="Figma",
        sources=SOURCES,
        source_workers=2,
        extra_scrapers=(scrape_newsroom,),
        max_entries=200,
        per_source_cap=100,
        dedupe_title_field=None,
        cache_transform=promote_cached_newsroom,
        # Keep native images, but do not fetch arbitrary article links for images.
        image_backfill=False,
        full=full,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate the Figma Atom feed")
    parser.add_argument("--full", action="store_true", help="Ignore cache and rebuild")
    sys.exit(0 if main(full=parser.parse_args().full) else 1)
