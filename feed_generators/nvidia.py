"""NVIDIA feed: official newsroom/blogs plus GeForce driver updates.

Native feeds cover NVIDIA Newsroom, the company blog, and the NVIDIA Developer
Blog. GeForce does not expose an equivalent public feed for driver posts, so
the two official GeForce surfaces are parsed directly: driver-tagged news and
the driver results page with versions, dates, highlights, and fixed-bug notes.
"""

import argparse
import re
import sys

from bs4 import BeautifulSoup
from multi_rss import get_html, parse_date, run
from utils import sanitize_xml

FEED_NAME = "nvidia"

SOURCES = [
    ("NVIDIA Newsroom", "https://nvidianews.nvidia.com/releases.xml", 60),
    ("NVIDIA Blog", "https://blogs.nvidia.com/feed/", 60),
    ("NVIDIA Developer Blog", "https://developer.nvidia.com/blog/feed/", 60),
]

GEFORCE_NEWS_URL = "https://www.nvidia.com/en-us/geforce/news/"
GEFORCE_DRIVER_RESULTS_URL = (
    "https://www.nvidia.com/Download/processFind.aspx?dtcid=1&lang=en-us&lid=1"
)
_NVIDIA_BASE_URL = "https://www.nvidia.com"
_MONTH_DATE = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|"
    r"Dec(?:ember)?)\s+\d{1,2},\s+20\d{2}"
)
_DRIVER_NEWS_RE = re.compile(
    r"\b(?:GeForce\s+)?(?:Game Ready|Studio)\s+Drivers?\b"
    r"|\b(?:Game Ready|Studio)\s+Driver\b",
    re.IGNORECASE,
)
_DRIVER_RELEASE_RE = re.compile(
    rf"(?P<kind>GeForce\s+Game\s+Ready|NVIDIA\s+Studio)\s+Driver\s*"
    rf"(?:WHQL\s*)?(?P<version>\d{{3}}\.\d{{2}})\s*"
    rf"(?P<date>{_MONTH_DATE})",
    re.IGNORECASE,
)
_DATE_RE = re.compile(rf"\b({_MONTH_DATE})\b", re.IGNORECASE)


def _absolute_nvidia_url(href):
    href = (href or "").split("?", 1)[0].split("#", 1)[0]
    if href.startswith("//"):
        return "https:" + href
    if href.startswith("/"):
        return _NVIDIA_BASE_URL + href
    return href


def parse_geforce_driver_news(html, known_links=None):
    known = {(link or "").rstrip("/") for link in (known_links or set())}
    soup = BeautifulSoup(html or "", "html.parser")
    seen = set()
    entries = []

    for anchor in soup.select("a[href]"):
        link = _absolute_nvidia_url(anchor.get("href", "")).rstrip("/")
        if not link.startswith(GEFORCE_NEWS_URL) or link == GEFORCE_NEWS_URL.rstrip("/"):
            continue
        if link in known or link in seen:
            continue

        heading = anchor.find(["h1", "h2", "h3", "h4"])
        title = (
            heading.get_text(" ", strip=True)
            if heading
            else anchor.get_text(" ", strip=True)
        )
        title = re.sub(r"\s+", " ", title).strip()

        card = anchor.find_parent(["article", "li"])
        if not _DRIVER_NEWS_RE.search(title) and card is not None:
            heading = card.find(["h1", "h2", "h3", "h4"])
            if heading is not None:
                title = re.sub(
                    r"\s+", " ", heading.get_text(" ", strip=True)
                ).strip()
        if not _DRIVER_NEWS_RE.search(title):
            continue

        scope = card or anchor.parent
        date = None
        description = ""
        for _ in range(6):
            if scope is None or getattr(scope, "name", None) in {"main", "body", "html"}:
                break
            text = re.sub(r"\s+", " ", scope.get_text(" ", strip=True)).strip()
            match = _DATE_RE.search(text)
            if match:
                date = parse_date(match.group(1))
                for paragraph in scope.find_all("p"):
                    value = re.sub(
                        r"\s+", " ", paragraph.get_text(" ", strip=True)
                    ).strip()
                    if value and value != title and not _DATE_RE.fullmatch(value):
                        description = value
                        break
                break
            scope = scope.parent

        if date is None:
            continue
        seen.add(link)
        entries.append(
            {
                "title": sanitize_xml(title[:200]),
                "link": link,
                "date": date,
                "description": sanitize_xml((description or title)[:500]),
                "source": "GeForce Driver News",
            }
        )

    entries.sort(key=lambda entry: entry["date"], reverse=True)
    return entries[:40]


def scrape_geforce_driver_news(known_links):
    html = get_html(GEFORCE_NEWS_URL)
    return parse_geforce_driver_news(html, known_links) if html else []


def parse_geforce_driver_results(html, known_links=None):
    known = set(known_links or set())
    text = re.sub(
        r"\s+",
        " ",
        BeautifulSoup(html or "", "html.parser").get_text(" ", strip=True),
    ).strip()
    matches = list(_DRIVER_RELEASE_RE.finditer(text))
    entries = []
    seen = set()

    for index, match in enumerate(matches):
        kind = (
            "NVIDIA Studio"
            if "studio" in match.group("kind").lower()
            else "GeForce Game Ready"
        )
        version = match.group("version")
        date = parse_date(match.group("date"))
        slug = f"{kind.lower().replace(' ', '-')}-{version.replace('.', '-')}"
        link = f"{GEFORCE_DRIVER_RESULTS_URL}#{slug}"
        if link in known or link in seen or date is None:
            continue

        next_start = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        details = text[match.end() : next_start].strip(" ·:;-")
        details = re.sub(r"\s+", " ", details)
        title = f"{kind} Driver {version} WHQL"
        seen.add(link)
        entries.append(
            {
                "title": sanitize_xml(title),
                "link": link,
                "date": date,
                "description": sanitize_xml((details or title)[:900]),
                "source": "GeForce Driver Changelog",
            }
        )

    entries.sort(key=lambda entry: entry["date"], reverse=True)
    return entries[:50]


def scrape_geforce_driver_results(known_links):
    html = get_html(GEFORCE_DRIVER_RESULTS_URL)
    return parse_geforce_driver_results(html, known_links) if html else []


def main(full=False):
    return run(
        feed_name=FEED_NAME,
        title="NVIDIA",
        subtitle=(
            "Official NVIDIA Newsroom, NVIDIA Blog, Developer Blog, and GeForce "
            "driver announcements/release notes."
        ),
        blog_url="https://nvidianews.nvidia.com/",
        author="NVIDIA",
        sources=SOURCES,
        extra_scrapers=[
            scrape_geforce_driver_news,
            scrape_geforce_driver_results,
        ],
        max_entries=240,
        per_source_cap={
            "": 60,
            "GeForce Driver News": 40,
            "GeForce Driver Changelog": 50,
        },
        full=full,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate the NVIDIA Atom feed")
    parser.add_argument(
        "--full", action="store_true", help="Ignore cache and rebuild from scratch"
    )
    sys.exit(0 if main(full=parser.parse_args().full) else 1)
