"""Combined development feed for Rust, Django and developer communities."""

import argparse
import json
import re
import sys
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from multi_rss import get_html, parse_date, run
from utils import sanitize_xml, setup_logging, stable_fallback_date

logger = setup_logging()

FEED_NAME = "development"

# Direct/original feeds come before the Django community aggregator so exact-link
# dedupe keeps the most specific source attribution.
SOURCES = [
    ("Rust Blog", "https://blog.rust-lang.org/feed.xml", 40),
    ("Inside Rust", "https://blog.rust-lang.org/inside-rust/feed.xml", 40),
    ("TestDriven.io", "https://testdriven.io/feed.xml", 30),
    ("Changelog News", "https://changelog.com/news/feed", 40),
    ("Scripting News", "http://scripting.com/rss.xml", 40),
    ("Development Seed", "https://developmentseed.org/rss.xml", 40),
    ("Coding Horror", "https://blog.codinghorror.com/rss/", 40),
    ("Carmine Paolino", "https://paolino.me/feed.xml", 30),
    ("RubyGems Blog", "https://blog.rubygems.org/atom.xml", 40),
    ("RubyInstaller", "https://rubyinstaller.org/feed.xml", 40),
    ("JetBrains Blog", "https://blog.jetbrains.com/feed/", 40),
    ("React Native Blog", "https://reactnative.dev/blog/rss.xml", 40),
    ("Ionic Framework Blog", "https://ionic.io/blog/tag/framework/feed", 40),
    ("web.dev Blog", "https://web.dev/blog/feed.xml", 40),
    ("Jupyter Blog", "https://blog.jupyter.org/feed", 40),
    ("Standard C++", "https://isocpp.org/blog/rss", 40),
    ("Django Weblog", "https://www.djangoproject.com/rss/weblog/", 30),
    ("Django News", "https://django-news.com/rss", 30),
    ("Django Packages latest", "https://djangopackages.org/feeds/packages/latest/atom/", 3),
    ("Django Community", "https://www.djangoproject.com/rss/community/blogs/", 40),
]

RUST_RELEASES_URL = "https://blog.rust-lang.org/releases/"
RUST_RELEASES_MAX = 30
DJANGO_PACKAGES_CHANGELOG_URL = "https://djangopackages.org/changelog/"
DJANGO_PACKAGES_CHANGELOG_MAX = 20
DEV_TOP_MONTH_URL = "https://dev.to/top/month"
DEV_TOP_MONTH_API_URL = "https://dev.to/api/articles?top=30&per_page=30"
DEV_TOP_MONTH_MAX = 30
JUSTJOIN_BLOG_URL = "https://justjoin.it/blog/"
JUSTJOIN_MAX = 15
_JUSTJOIN_POST_RE = re.compile(r"^https://justjoin\.it/blog/[^/?#]+/?$", re.I)
_JUSTJOIN_DATE_RE = re.compile(
    r"\b\d{1,2}\s+(?:stycznia|lutego|marca|kwietnia|maja|czerwca|lipca|"
    r"sierpnia|września|października|listopada|grudnia)\s+20\d{2}\b", re.I
)

_RUST_RELEASE_DATE = re.compile(r"/(20\d{2})/(\d{2})/(\d{2})/")


def scrape_rust_releases(known_links):
    """Read the official Rust releases index.

    The page is a release-only subset of the main Rust blog. Keeping it as a
    source gives the aggregate deeper release history; shared link dedupe removes
    announcements already present in the main blog feed.
    """
    html = get_html(RUST_RELEASES_URL)
    if not html:
        logger.warning("  [Rust Releases] fetch failed; continuing")
        return []

    soup = BeautifulSoup(html, "html.parser")
    entries, seen = [], set()
    matched = 0
    for anchor in soup.find_all("a", href=True):
        title = anchor.get_text(" ", strip=True)
        if not title.startswith("Announcing Rust"):
            continue
        matched += 1
        link = urljoin(RUST_RELEASES_URL, anchor["href"])
        if link in known_links or link in seen:
            continue
        seen.add(link)

        match = _RUST_RELEASE_DATE.search(link)
        date = parse_date("-".join(match.groups())) if match else None
        entries.append(
            {
                "title": sanitize_xml(title),
                "link": link,
                "date": date or stable_fallback_date(link),
                "description": sanitize_xml(title),
                "source": "Rust Releases",
            }
        )
        if len(entries) >= RUST_RELEASES_MAX:
            break
    if matched == 0:
        logger.warning("  [Rust Releases] no release links matched the index layout")
    return entries


def scrape_django_packages_changelog(known_links):
    """Read dated entries from the Django Packages changelog page."""
    html = get_html(DJANGO_PACKAGES_CHANGELOG_URL)
    if not html:
        logger.warning("  [Django Packages changelog] fetch failed; continuing")
        return []

    soup = BeautifulSoup(html, "html.parser")
    entries, seen = [], set()
    for heading in soup.find_all("h2"):
        anchor = heading.find("a", href=True)
        if not anchor or "/changelog/" not in anchor["href"]:
            continue
        link = urljoin(DJANGO_PACKAGES_CHANGELOG_URL, anchor["href"])
        if link.rstrip("/") == DJANGO_PACKAGES_CHANGELOG_URL.rstrip("/"):
            continue
        if link in known_links or link in seen:
            continue

        date_node = heading.parent.select_one(".text-muted-foreground")
        date_text = date_node.get_text(" ", strip=True) if date_node else ""
        date = parse_date(date_text) if date_text else None
        title = anchor.get_text(" ", strip=True)
        if not title:
            continue

        seen.add(link)
        entries.append(
            {
                "title": sanitize_xml(title),
                "link": link,
                "date": date or stable_fallback_date(link),
                "description": sanitize_xml(title),
                "source": "Django Packages changelog",
            }
        )
        if len(entries) >= DJANGO_PACKAGES_CHANGELOG_MAX:
            break
    return entries


def scrape_dev_top_month(known_links):
    """Read DEV's top articles from the last 30 days via its public API."""
    payload = get_html(DEV_TOP_MONTH_API_URL)
    if not payload:
        logger.warning("  [DEV Top Month] fetch failed; continuing")
        return []
    try:
        articles = json.loads(payload)
    except json.JSONDecodeError as exc:
        logger.warning("  [DEV Top Month] invalid JSON: %s", exc)
        return []
    if not isinstance(articles, list):
        logger.warning("  [DEV Top Month] unexpected payload shape")
        return []

    entries = []
    for article in articles[:DEV_TOP_MONTH_MAX]:
        if not isinstance(article, dict):
            continue
        link = article.get("url")
        title = article.get("title")
        if not isinstance(link, str) or not link or link in known_links:
            continue
        if not isinstance(title, str) or not title.strip():
            continue
        title = sanitize_xml(title.strip())
        description = article.get("description")
        description = (
            sanitize_xml(description.strip())
            if isinstance(description, str) and description.strip()
            else title
        )
        published = article.get("published_at")
        date = parse_date(published) if published else None
        entries.append(
            {
                "title": title,
                "link": link,
                "date": date or stable_fallback_date(link),
                "description": description,
                "source": "DEV Top Month",
                "image": article.get("cover_image") or article.get("social_image"),
            }
        )
    return entries


def justjoin_article_links(html, known_links=None):
    """Discover Just Geek IT article URLs, excluding categories and duplicates."""
    known_links = known_links or set()
    soup = BeautifulSoup(html, "html.parser")
    links, seen = [], set()
    for anchor in soup.find_all("a", href=True):
        link = urljoin(JUSTJOIN_BLOG_URL, anchor["href"])
        link = link.split("#", 1)[0].split("?", 1)[0].rstrip("/")
        if not _JUSTJOIN_POST_RE.fullmatch(link) or link in known_links or link in seen:
            continue
        seen.add(link)
        links.append(link)
    return links[:JUSTJOIN_MAX]


def scrape_justjoin_blog(known_links):
    """Extract post metadata from Just Geek IT, skipping unavailable detail pages."""
    index = get_html(JUSTJOIN_BLOG_URL)
    if not index:
        logger.warning("  [Just Geek IT] blog index unavailable")
        return []

    entries = []
    for link in justjoin_article_links(index, known_links):
        html = get_html(link)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        heading = soup.find("h1")
        title_meta = soup.find("meta", attrs={"property": "og:title"})
        title = (
            heading.get_text(" ", strip=True)
            if heading
            else title_meta.get("content", "") if title_meta else ""
        )
        title = sanitize_xml(title)
        if not title:
            continue

        desc_meta = soup.find("meta", attrs={"name": "description"})
        description = (
            sanitize_xml(desc_meta.get("content", "").strip()) if desc_meta else ""
        )
        published = soup.find("meta", attrs={"property": "article:published_time"})
        timestamp = published.get("content") if published else None
        if not timestamp:
            time_tag = soup.find("time", datetime=True)
            timestamp = time_tag["datetime"] if time_tag else None
        if not timestamp:
            date_match = _JUSTJOIN_DATE_RE.search(soup.get_text(" ", strip=True)[:4000])
            timestamp = date_match.group(0) if date_match else None

        image_meta = soup.find("meta", attrs={"property": "og:image"})
        entries.append(
            {
                "title": title,
                "link": link,
                "date": (parse_date(timestamp) if timestamp else None)
                or stable_fallback_date(link),
                "description": description or title,
                "source": "Just Geek IT",
                "image": image_meta.get("content") if image_meta else None,
            }
        )
    logger.info("  [Just Geek IT] found %d article(s)", len(entries))
    return entries


def main(full=False):
    return run(
        feed_name=FEED_NAME,
        title="Development",
        subtitle="Combined Rust, Django, developer blogs, and ecosystem updates.",
        blog_url="https://blog.rust-lang.org/",
        author="development communities",
        sources=SOURCES,
        extra_scrapers=[
            scrape_rust_releases,
            scrape_django_packages_changelog,
            scrape_dev_top_month,
            scrape_justjoin_blog,
        ],
        max_entries=300,
        source_workers=6,
        full=full,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate the combined development feed")
    parser.add_argument("--full", action="store_true", help="Ignore cache and rebuild from scratch")
    sys.exit(0 if main(full=parser.parse_args().full) else 1)
