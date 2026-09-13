"""Spotify ecosystem feed: Spotify updates plus DistroKid artist tooling news."""

import argparse
import sys
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from multi_rss import get_html, parse_date, run
from utils import sanitize_xml

FEED_NAME = "spotify"
DISTROKID_BLOG_URL = "https://distrokid.com/resources/blog"
DISTROKID_LABEL = "DistroKid Blog"

SOURCES = [
    ("Spotify Newsroom", "https://newsroom.spotify.com/feed/", 20),
    ("Spotify for Developers", "https://developer.spotify.com/rss.xml", 40),
]


def _parse_distrokid_page(html, known_links, seen):
    """Parse one server-rendered Webflow page from the DistroKid blog."""
    soup = BeautifulSoup(html or "", "html.parser")
    entries = []
    for anchor in soup.select("a[href^='/resources/blog/']"):
        href = anchor.get("href", "").split("?", 1)[0].split("#", 1)[0]
        link = urljoin(DISTROKID_BLOG_URL, href)
        if not href or link in known_links or link in seen:
            continue
        heading = anchor.find(["h2", "h3"])
        if not heading:
            continue
        title = sanitize_xml(heading.get_text(" ", strip=True))
        if not title:
            continue
        published = None
        for node in anchor.select(
            ".wd_blog-featured-published-date, .wd_text-size-small.wd_text-color-gray400"
        ):
            published = parse_date(node.get_text(" ", strip=True))
            if published:
                break
        if not published:
            continue
        description_el = anchor.find("p")
        description = (
            sanitize_xml(description_el.get_text(" ", strip=True))
            if description_el
            else title
        )
        image_el = anchor.find("img", src=True)
        seen.add(link)
        entries.append(
            {
                "id": link,
                "title": title,
                "link": link,
                "date": published,
                "description": description[:500] or title,
                "source": DISTROKID_LABEL,
                "image": image_el.get("src") if image_el else None,
            }
        )
    next_link = soup.select_one("a.w-pagination-next[href]")
    return entries, (urljoin(DISTROKID_BLOG_URL, next_link["href"]) if next_link else None)


def scrape_distrokid_blog(known_links):
    """Collect DistroKid blog pages, following Webflow pagination defensively."""
    entries = []
    seen = set()
    url = DISTROKID_BLOG_URL
    for _ in range(5):
        html = get_html(url)
        if not html:
            break
        page_entries, next_url = _parse_distrokid_page(html, known_links, seen)
        entries.extend(page_entries)
        if not next_url or next_url == url:
            break
        url = next_url
    return entries


def doc_sources():
    # Keep Spotify as the primary docs icon while exposing the procedural source.
    return [
        ("Spotify Newsroom", "https://newsroom.spotify.com/feed/"),
        (DISTROKID_LABEL, DISTROKID_BLOG_URL),
    ]


def main(full=False):
    return run(
        feed_name=FEED_NAME,
        title="Spotify",
        subtitle="Spotify newsroom and developer-platform updates, plus DistroKid "
        "music-distribution and artist-tooling news.",
        blog_url="https://newsroom.spotify.com/",
        author="various",
        sources=SOURCES,
        extra_scrapers=(scrape_distrokid_blog,),
        max_entries=150,
        per_source_cap=60,
        full=full,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate the Spotify Atom feed")
    parser.add_argument("--full", action="store_true", help="Ignore cache and rebuild from scratch")
    sys.exit(0 if main(full=parser.parse_args().full) else 1)
