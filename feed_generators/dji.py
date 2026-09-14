"""DJI feed: announcements, ViewPoints posts, and community forum threads."""

import argparse
import re
import sys
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from multi_rss import get_html, parse_date, run
from utils import sanitize_xml

FEED_NAME = "dji"
ANNOUNCEMENTS_URL = "https://www.dji.com/pl/mobile/media-center/announcements"
VIEWPOINTS_URL = "https://viewpoints.dji.com/blog?site=brandsite"
FORUM_URL = "https://forum.dji.com/?site=brandsite&from=nav"

ISO_DATE_RE = re.compile(r"\b20\d{2}[-/]\d{1,2}[-/]\d{1,2}\b")
MONTH_DATE_RE = re.compile(
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+"
    r"\d{1,2},\s+20\d{2}\b",
    re.IGNORECASE,
)
FORUM_HREF_RE = re.compile(r"(?:thread-\d+|forum\.php\?[^#]*\bmod=viewthread\b)")


def _nearest_date(anchor, pattern):
    node = anchor
    for _ in range(5):
        node = getattr(node, "parent", None)
        if node is None:
            break
        text = node.get_text(" ", strip=True)
        if len(text) > 3500:
            break
        match = pattern.search(text)
        if match:
            return match.group(0)
    return ""


def _entries_from_listing(html, *, base_url, source, href_test, date_pattern, cap=60):
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    entries = []
    seen = set()

    for anchor in soup.find_all("a", href=True):
        href = anchor.get("href", "").strip()
        if not href_test(href):
            continue
        link = urljoin(base_url, href)
        if link in seen:
            continue

        title = sanitize_xml(anchor.get_text(" ", strip=True))
        if not title or title.casefold() in {"read more", "more", "next", "previous"}:
            continue

        date_text = _nearest_date(anchor, date_pattern)
        if date_text:
            title = re.sub(re.escape(date_text), "", title, flags=re.IGNORECASE).strip(" -–—|·")
        if source == "DJI Announcements":
            title = re.sub(r"^(?:News|Product Releases?)\s+", "", title, flags=re.IGNORECASE)
        title = re.sub(r"\s+", " ", title).strip()
        if len(title) < 8:
            continue

        entries.append(
            {
                "title": title,
                "link": link,
                "date": parse_date(date_text) if date_text else None,
                "description": title,
                "source": source,
            }
        )
        seen.add(link)
        if len(entries) >= cap:
            break

    return entries


def scrape_announcements(known_links):
    html = get_html(ANNOUNCEMENTS_URL)
    entries = _entries_from_listing(
        html,
        base_url=ANNOUNCEMENTS_URL,
        source="DJI Announcements",
        href_test=lambda href: "/media-center/announcements/" in href,
        date_pattern=ISO_DATE_RE,
    )
    return [entry for entry in entries if entry["link"] not in known_links]


def scrape_viewpoints(known_links):
    html = get_html(VIEWPOINTS_URL)
    entries = _entries_from_listing(
        html,
        base_url=VIEWPOINTS_URL,
        source="DJI ViewPoints",
        href_test=lambda href: "/blog/" in href and href.rstrip("/") != "/blog",
        date_pattern=MONTH_DATE_RE,
    )
    return [entry for entry in entries if entry["link"] not in known_links]


def scrape_forum(known_links):
    html = get_html(FORUM_URL)
    entries = _entries_from_listing(
        html,
        base_url=FORUM_URL,
        source="DJI Forum",
        href_test=lambda href: bool(FORUM_HREF_RE.search(href)),
        date_pattern=ISO_DATE_RE,
        cap=80,
    )
    return [entry for entry in entries if entry["link"] not in known_links]


def doc_sources():
    return [
        ("DJI Announcements", ANNOUNCEMENTS_URL),
        ("DJI ViewPoints", VIEWPOINTS_URL),
        ("DJI Forum", FORUM_URL),
    ]


def main(full=False):
    return run(
        feed_name=FEED_NAME,
        title="DJI",
        subtitle="DJI announcements, ViewPoints articles, and community forum threads.",
        blog_url=ANNOUNCEMENTS_URL,
        author="DJI",
        extra_scrapers=(scrape_announcements, scrape_viewpoints, scrape_forum),
        max_entries=250,
        per_source_cap=100,
        full=full,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate the DJI Atom feed")
    parser.add_argument("--full", action="store_true", help="Ignore cache and rebuild from scratch")
    sys.exit(0 if main(full=parser.parse_args().full) else 1)
