"""Curated Polish meme sites combined into one Atom/MRSS + Model Feed.

The sites have HTML listings but no verified stable native feeds. Parse listing
permalinks and available media rather than guessing publication dates.
"""
import argparse
import re
import sys
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup
from multi_rss import get_html, parse_date, run
from utils import sanitize_xml

FEED_NAME = "memy"
MEMY_URL = "https://memy.pl/"
JEJA_URL = "https://memy.jeja.pl/"
KWEJK_URL = "https://kwejk.pl/"
SITES = (
    ("Memy.pl", MEMY_URL, re.compile(r"^/mem/\d+/[^/]+/?$")),
    ("Jeja.pl", JEJA_URL, re.compile(r"^/\d+,[^/]+\.html$")),
    ("Kwejk.pl", KWEJK_URL, re.compile(r"^/obrazek/\d+/[^/]+\.html$")),
)
MAX_PER_SITE = 25
_IMAGE_KEYS = ("data-original", "data-src", "data-lazy-src", "src")


def _image(card, base):
    """First usable attached image, ignoring empty placeholders and data URIs."""
    for img in card.select("picture source, img, video"):
        if img.name == "source" and (img.get("type") or "").startswith("video/"):
            continue
        candidates = ([img.get("poster")] if img.name == "video" else [
            img.get(key) for key in _IMAGE_KEYS
        ] + [img.get("srcset"), img.get("data-srcset")])
        for raw in candidates:
            if not raw:
                continue
            candidate = str(raw).split(",", 1)[0].strip().split(" ", 1)[0]
            if not candidate or candidate.startswith(("data:", "blob:")):
                continue
            try:
                url = urljoin(base, candidate)
                parts = urlsplit(url)
            except ValueError:
                continue
            if parts.scheme == "https" and not parts.path.lower().endswith(
                (".mp4", ".webm", ".mov", ".m3u8")
            ):
                return url
    return None


def _card(anchor):
    """Find a local content card; never fall through to the entire page."""
    for ancestor in list(anchor.parents)[:6]:
        if ancestor.name not in {"article", "li", "div", "section"}:
            continue
        classes = " ".join(ancestor.get("class", [])).lower()
        if ancestor.name == "article" or any(
            marker in classes for marker in
            ("post", "meme", "image", "obraz", "box", "item", "entry", "card")
        ):
            return ancestor
    return anchor.parent


def parse_listing(html, label, base, path_pattern, known_links):
    soup = BeautifulSoup(html, "html.parser")
    entries = []
    seen = set()
    for anchor in soup.select("a[href]"):
        raw = anchor.get("href", "")
        try:
            url = urljoin(base, raw)
            parts = urlsplit(url)
        except ValueError:
            continue
        if parts.scheme != "https" or parts.netloc.lower() not in {
            urlsplit(base).netloc, "www." + urlsplit(base).netloc
        }:
            continue
        if not path_pattern.fullmatch(parts.path):
            continue
        link = f"https://{urlsplit(base).netloc}{parts.path}"
        if link in seen or link in known_links:
            continue
        card = _card(anchor)
        heading = anchor.find(["h1", "h2", "h3"]) or anchor.find_parent(["h1", "h2", "h3"])
        title = (heading or anchor).get_text(" ", strip=True)
        if not title:
            heading = card.find(["h1", "h2", "h3"])
            title = heading.get_text(" ", strip=True) if heading else ""
        if not title:
            continue
        date_el = card.find("time", datetime=True)
        published = parse_date(date_el["datetime"]) if date_el else None
        img = _image(card, base)
        title = sanitize_xml(title)
        entries.append({
            "title": title,
            "link": link,
            "date": published,
            "description": title,
            "source": label,
            "image": img,
        })
        seen.add(link)
        if len(entries) >= MAX_PER_SITE:
            break
    return entries


def scrape_meme_sites(known_links):
    entries = []
    for label, url, pattern in SITES:
        try:
            html = get_html(url)
            if not html:
                continue
            found = parse_listing(html, label, url, pattern, known_links)
        except (ValueError, TypeError) as exc:
            from multi_rss import logger
            logger.warning("Could not parse %s: %s", label, exc)
            continue
        first_seen = datetime.now(timezone.utc)
        for index, entry in enumerate(found):
            if entry["date"] is None:
                # Order the listing newest-first without claiming upload dates.
                entry["date"] = first_seen - timedelta(seconds=index)
                entry["date_kind"] = "first_seen"
        entries.extend(found)
    return entries


def doc_sources():
    return [(label, url) for label, url, _ in SITES]


def main(full=False):
    return run(
        feed_name=FEED_NAME,
        title="Memy",
        subtitle="Images, GIFs and memes from Memy.pl, Jeja.pl and Kwejk.pl.",
        blog_url=MEMY_URL,
        author="Memy.pl · Jeja.pl · Kwejk.pl",
        extra_scrapers=[scrape_meme_sites],
        max_entries=300,
        per_source_cap={label: 100 for label, _, _ in SITES},
        language="pl",
        dedupe_title_field=None,
        full=full,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate the Memy Atom feed")
    parser.add_argument("--full", action="store_true")
    sys.exit(0 if main(full=parser.parse_args().full) else 1)
