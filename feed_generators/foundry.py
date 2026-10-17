"""Combined Foundry / IDG publications: native RSS plus Foundry's resource index.

The HTML sitemap is a curated, dated resource listing rather than an XML
sitemap. Reading its first page catches research and press resources that may
not appear in Foundry's native blog feed.
"""

import argparse
import re
import sys
from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup, NavigableString, Tag
import multi_rss

FEED_NAME = "foundry"
SITEMAP_URL = "https://foundryco.com/sitemap/"

SOURCES = [
    ("Foundry Blog", "https://foundryco.com/feed/", 40),
    ("CSO", "https://www.csoonline.com/feed", 40),
    ("CIO", "https://www.cio.com/feed", 40),
    ("PCWorld", "https://www.pcworld.com/feed", 40),
    ("Computerworld", "https://www.computerworld.com/feed", 40),
    ("InfoWorld", "https://www.infoworld.com/feed", 40),
]

_DATE_RE = re.compile(
    r"^(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
    r"[a-z]*\s+\d{1,2},\s+20\d{2}$",
    re.IGNORECASE,
)
_HEADINGS = {"h1", "h2", "h3", "h4", "h5", "h6"}


def _nearby_date(heading):
    """Use only the date next to this card, never a later card's date."""
    examined = 0
    for node in heading.next_elements:
        if isinstance(node, Tag) and node.name in _HEADINGS:
            break
        if not isinstance(node, NavigableString):
            continue
        value = str(node).strip()
        if not value:
            continue
        examined += 1
        if _DATE_RE.fullmatch(value):
            return multi_rss.parse_date(value)
        if examined >= 15:
            break
    return None


def parse_sitemap(html, known_links):
    """Read dated h4 article cards; ignore menus, pagination and event dates."""
    soup = BeautifulSoup(html, "html.parser")
    entries = []
    seen = set(known_links)
    for heading in soup.select("h4"):
        anchor = heading.find("a", href=True)
        if anchor is None:
            continue
        link = urljoin(SITEMAP_URL, anchor["href"]).split("#", 1)[0]
        parsed = urlsplit(link)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or link in seen:
            continue
        title = multi_rss.sanitize_xml(anchor.get_text(" ", strip=True))
        date = _nearby_date(heading)
        if not title or date is None or date.date() > datetime.now(timezone.utc).date():
            continue
        seen.add(link)
        entries.append({
            "title": title,
            "link": link,
            "date": date,
            "description": title,
            "source": "Foundry Resources",
        })
    return entries


def scrape_sitemap(known_links):
    html = multi_rss.get_html(SITEMAP_URL)
    if not html:
        return []
    return parse_sitemap(html, known_links)


def main(full=False):
    return multi_rss.run(
        feed_name=FEED_NAME,
        title="Foundry",
        subtitle="Foundry research and news from CSO, CIO, PCWorld, "
                 "Computerworld, and InfoWorld.",
        blog_url=SITEMAP_URL,
        author="Foundry",
        sources=SOURCES,
        source_workers=6,
        extra_scrapers=(scrape_sitemap,),
        max_entries=300,
        per_source_cap=55,
        dedupe_title_field=None,
        full=full,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate the Foundry Atom feed")
    parser.add_argument("--full", action="store_true", help="Ignore cache and rebuild")
    sys.exit(0 if main(full=parser.parse_args().full) else 1)
