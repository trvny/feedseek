"""Link-only digest from The Independent and Indy100."""

import argparse
import sys
from datetime import UTC, datetime, timedelta
from urllib.parse import urljoin, urlsplit, urlunsplit

import feedparser
from bs4 import BeautifulSoup
from multi_rss import get_html, parse_date, run
from utils import sanitize_xml

FEED_NAME = "independent"
BASE_URL = "https://www.independent.co.uk/"
INDY_URL = "https://www.indy100.com/"
INDEPENDENT_RSS = BASE_URL + "rss"
INDY_RSS = INDY_URL + "feeds/feed.rss"
SOURCES = [
    ("The Independent", INDEPENDENT_RSS),
    ("Indy100 RSS", INDY_RSS),
    ("Indy100 homepage", INDY_URL),
]
INDY_SECTIONS = {
    "news", "politics", "viral", "gaming", "celebrities", "science-tech",
    "sport", "showbiz", "tv", "lifestyle", "identities", "tiktok", "video",
}
CAP = 60


def publisher_link(value, base):
    """Keep direct publisher article links; strip tracking and fragments."""
    parsed = urlsplit(urljoin(base, value or ""))
    host = urlsplit(base).hostname
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in {host, host.removeprefix("www.")}:
        return None
    parts = parsed.path.strip("/").split("/")
    if len(parts) < 2:
        return None
    if base == INDY_URL and parts[0] not in INDY_SECTIONS:
        return None
    return urlunsplit(("https", host, parsed.path.rstrip("/"), "", ""))


def entry(title, link, label, date=None):
    title = sanitize_xml(" ".join(title.split()))
    if not title or not link:
        return None
    return {
        "title": title,
        "link": link,
        "description": title,
        "source": label,
        "date": date or datetime.now(UTC),
        "date_kind": "published" if date else "first_seen",
    }


def parse_rss(xml, base, label):
    feed = feedparser.parse(xml or "")
    out = []
    seen = set()
    for item in feed.entries:
        link = publisher_link(item.get("link", ""), base)
        if not link or link in seen:
            continue
        date = parse_date(item["published"]) if item.get("published") else None
        record = entry(BeautifulSoup(item.get("title", ""), "html.parser").get_text(" ", strip=True), link, label, date)
        if record:
            out.append(record)
            seen.add(link)
        if len(out) >= CAP:
            break
    return out


def parse_indy_listing(html):
    """Use article heading links, not topic/tag navigation or ranking widgets."""
    soup = BeautifulSoup(html or "", "html.parser")
    out = []
    seen = set()
    for heading in soup.find_all(["h2", "h3"]):
        anchor = heading.find("a", href=True) or heading.find_parent("a", href=True)
        if not anchor:
            continue
        link = publisher_link(anchor["href"], INDY_URL)
        if not link or link in seen:
            continue
        if heading.find_parent(["nav", "header", "footer", "aside"]):
            continue
        # Short section/topic slugs (e.g. /politics/trump) are navigation.
        # Allow short article slugs only within explicit article markup.
        slug = urlsplit(link).path.rsplit("/", 1)[-1]
        if len(slug.split("-")) < 3 and not heading.find_parent("article"):
            continue
        record = entry(heading.get_text(" ", strip=True), link, "Indy100")
        if record:
            out.append(record)
            seen.add(link)
        if len(out) >= CAP:
            break
    return out


def scrape_independent(known_links):
    rows = parse_rss(get_html(INDEPENDENT_RSS), BASE_URL, "The Independent")
    return [row for row in rows if row["link"] not in known_links]


def scrape_indy100(known_links):
    rows = parse_rss(get_html(INDY_RSS), INDY_URL, "Indy100")
    cutoff = datetime.now(UTC) - timedelta(days=7)
    fresh = [
        row for row in rows
        if row["date_kind"] == "published" and row["date"] >= cutoff
    ]
    # The native endpoint can return a valid but abandoned feed.
    if not fresh or not any(row["link"] not in known_links for row in fresh):
        rows = parse_indy_listing(get_html(INDY_URL))
    else:
        rows = fresh
    return [row for row in rows if row["link"] not in known_links]


def main(full=False):
    return run(
        feed_name=FEED_NAME,
        title="The Independent + Indy100",
        subtitle="Headlines and direct article links from The Independent and Indy100.",
        blog_url=BASE_URL,
        author="The Independent / Indy100",
        extra_scrapers=(scrape_independent, scrape_indy100),
        max_entries=200,
        per_source_cap=100,
        image_backfill=False,
        full=full,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate the Independent + Indy100 Atom feed")
    parser.add_argument("--full", action="store_true", help="Ignore cache and rebuild from scratch")
    sys.exit(0 if main(full=parser.parse_args().full) else 1)
