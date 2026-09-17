"""Generate Atom feed for Czwórka — Polskie Radio
(https://czworka.online/).

Czwórka runs on Polskie Radio's classic server-rendered ASP.NET CMS. The
homepage is fully static (no Selenium needed), but it's built almost entirely
from dateless promo carousels, and card titles have category labels glued on
("KulturaRuszyły zdjęcia…"). So the homepage is used only to *discover* article
links; the clean title, lead, and publish timestamp are read from each article
page's metadata:

* title  -> ``og:title``
* lead   -> ``og:description``
* date   -> ``span.time`` inside the main ``div.this-article`` header
            (``DD.MM.YYYY HH:MM``, Europe/Warsaw)

The homepage embeds cross-promo boxes for other Polskie Radio stations
(Jedynka ``/7/`` etc.); only Czwórka articles (``/10/`` portal) are kept.

A JSON cache (``cache/czworka_posts.json``) accumulates history across hourly
runs and dedupes by canonical article id. Because already-cached articles are
skipped, the per-article fetch only happens once per article — a full run pays
for all of them, incremental runs only for genuinely new ones. Writes an Atom
feed to ``feeds/feed_czworka.xml``.
"""

import argparse
import re
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
from enrich import enrich_entries
from feedgen.feed import FeedGenerator
from utils import (
    add_entry_media,
    deserialize_entries,
    fetch_page,
    load_cache,
    localize_wall_time,
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

logger = setup_logging()

FEED_NAME = "czworka"
BLOG_URL = "https://czworka.online/"
FETCH_BASE_URL = "https://czworka.online"
PUBLIC_BASE_URL = "https://www.polskieradio.pl"
ARTICLE_FETCH_BASE_URLS = (PUBLIC_BASE_URL, FETCH_BASE_URL)
HOMEPAGE_URLS = (
    BLOG_URL,
    "https://www.polskieradio.pl/10",
    "https://www.polskieradio.pl/10,Czworka",
)
WARSAW = ZoneInfo("Europe/Warsaw")

# Czwórka is portal id 10; article links look like /10/{sub}/Artykul/{id}[,slug].
_CZWORKA_LINK_RE = re.compile(r"^/10/\d+/Artykul/\d+", re.I)
_ARTICLE_ID_RE = re.compile(r"/Artykul/(\d+)", re.I)
_DATETIME_RE = re.compile(r"(\d{2})\.(\d{2})\.(\d{4})\s+(\d{2}):(\d{2})")
_SOURCE_HOST_RE = re.compile(r"^https?://(?:www\.polskieradio\.pl|czworka\.online)", re.I)

# Be polite during the big initial crawl.
FETCH_DELAY_SECONDS = 0.4


def _canonical(link: str) -> str:
    """Keep the historical public host and drop the trailing article slug."""
    link = _SOURCE_HOST_RE.sub(PUBLIC_BASE_URL, link)
    return re.sub(r"(/Artykul/\d+),.*$", r"\1", link)


def _fetch_urls(href: str) -> list[str]:
    """Return article fetch candidates, preferring the canonical public host."""
    if href.startswith("/"):
        return [f"{base}{href}" for base in ARTICLE_FETCH_BASE_URLS]
    return [_SOURCE_HOST_RE.sub(base, href) for base in ARTICLE_FETCH_BASE_URLS]


def _fetch_url(href: str) -> str:
    return _fetch_urls(href)[0]


def _meta(soup: BeautifulSoup, prop: str) -> str | None:
    tag = soup.find("meta", attrs={"property": prop}) or soup.find("meta", attrs={"name": prop})
    return tag.get("content") if tag else None


def _parse_article_date(soup: BeautifulSoup, fallback_id: str) -> datetime:
    """Read the article-header timestamp (DD.MM.YYYY HH:MM) scoped to the main
    article container so sidebar/related dates don't leak in."""
    main = soup.find("div", class_="this-article") or soup
    for span in main.find_all("span", class_="time"):
        m = _DATETIME_RE.search(span.get_text(strip=True))
        if m:
            day, month, year, hh, mm = (int(g) for g in m.groups())
            try:
                return localize_wall_time(datetime(year, month, day, hh, mm), WARSAW)
            except ValueError:
                break
    at = main.find("div", class_="article-time")
    if at:
        m = _DATETIME_RE.search(at.get_text(strip=True))
        if m:
            day, month, year, hh, mm = (int(g) for g in m.groups())
            try:
                return localize_wall_time(datetime(year, month, day, hh, mm), WARSAW)
            except ValueError:
                pass
    return stable_fallback_date(fallback_id)


def discover_links(html: str) -> list[str]:
    """Collect unique Czwórka article URLs from the listing page."""
    soup = BeautifulSoup(html, "html.parser")
    seen: set[str] = set()
    links: list[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not _CZWORKA_LINK_RE.match(href):
            continue
        full = _fetch_url(href)
        canon = _canonical(full)
        if canon in seen:
            continue
        seen.add(canon)
        links.append(full)
    logger.info("Discovered %d Czwórka article links", len(links))
    return links


def fetch_homepage_links(retries: int = 3, backoff: float = 2.0) -> list[str]:
    """Fetch Czwórka links, preferring its dedicated host over legacy aliases."""
    for attempt in range(1, retries + 1):
        for url in HOMEPAGE_URLS:
            try:
                html = fetch_page(url, timeout=15)
            except Exception as exc:
                logger.warning(
                    "Fetch failed for %s (attempt %d/%d): %s",
                    url,
                    attempt,
                    retries,
                    exc,
                )
                continue

            links = discover_links(html)
            if links:
                return links
            logger.warning("No Czwórka article links found at %s", url)

        if attempt < retries:
            time.sleep(backoff * attempt)
    return []


def fetch_article(url: str) -> dict | None:
    """Fetch a single article page and extract title, lead, and date."""
    html = None
    for candidate in _fetch_urls(url):
        try:
            html = fetch_page(candidate, timeout=15)
            break
        except Exception as exc:
            logger.warning("Failed to fetch %s: %s", candidate, exc)
    if html is None:
        return None

    soup = BeautifulSoup(html, "html.parser")
    title = _meta(soup, "og:title")
    if not title:
        h1 = soup.find("h1")
        title = h1.get_text(strip=True) if h1 else None
    if not title:
        logger.warning("No title for %s; skipping", url)
        return None

    lead = _meta(soup, "og:description") or ""
    image = _meta(soup, "og:image")
    canon = _canonical(url)
    date = _parse_article_date(soup, canon)

    return {
        "link": canon,
        "title": sanitize_xml(title.strip()),
        "description": sanitize_xml(lead.strip()) or sanitize_xml(title.strip()),
        "date": date,
        "image": image,
    }


def fetch_new_articles(links: list[str], known: set[str]) -> tuple[list[dict], list[str]]:
    """Fetch uncached articles and report any that failed on every host."""
    posts: list[dict] = []
    failed: list[str] = []
    for url in links:
        canonical = _canonical(url)
        if canonical in known:
            continue
        post = fetch_article(url)
        if post:
            posts.append(post)
        else:
            failed.append(canonical)
        time.sleep(FETCH_DELAY_SECONDS)
    logger.info("Fetched %d new article pages", len(posts))
    return posts, failed


def generate_rss_feed(posts: list[dict]) -> FeedGenerator:
    fg = FeedGenerator()
    fg.id("https://www.polskieradio.pl/10,czworka")
    fg.title("PR4 Czwórka")
    fg.description(
        "Najnowsze artykuły Czwórki Polskiego Radia: muzyka, życie, kultura "
        "i audycje czwartego programu."
    )
    fg.language("pl")
    fg.author({"name": "Polskie Radio – Czwórka"})
    fg.icon("https://www.polskieradio.pl/favicon.ico")
    fg.subtitle("Czwarty program Polskiego Radia")
    setup_feed_links(fg, blog_url=BLOG_URL, feed_name=FEED_NAME)
    setup_feed_extensions(fg)

    for post in posts:
        fe = fg.add_entry()
        fe.title(post["title"])
        fe.description(post["description"])
        fe.link(href=post["link"])
        fe.id(post["link"])
        if post.get("date"):
            fe.published(post["date"])
        add_entry_media(fe, post.get("image"))

    logger.info("Generated Atom feed with %d entries", len(posts))
    return fg


def main(full_reset: bool = False) -> bool:
    cache = load_cache(FEED_NAME)
    cached_entries = deserialize_entries(cache.get("entries", []))
    known = set() if full_reset else {e["link"] for e in cached_entries}

    links = fetch_homepage_links()
    if not links:
        logger.warning("Czwórka homepage unavailable after retries — keeping the last good feed")
        return False

    new_posts, failed_articles = fetch_new_articles(links, known)
    if failed_articles:
        logger.warning(
            "Failed to fetch %d new Czwórka article(s) — keeping the last good feed",
            len(failed_articles),
        )
        return False

    if full_reset or not cached_entries:
        mode = "full reset" if full_reset else "no cache exists"
        logger.info("Running full fetch (%s)", mode)
        posts = sort_posts_for_feed(new_posts, date_field="date")
    else:
        logger.info("Running incremental update")
        posts = merge_entries(new_posts, cached_entries)

    enrich_entries(posts)
    if not posts:
        logger.warning("No posts fetched — skipping feed update to avoid overwriting with empty feed")
        return False

    save_cache(FEED_NAME, posts)
    feed = generate_rss_feed(posts)
    save_atom_feed(feed, FEED_NAME)
    logger.info("Done!")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Czwórka (Polskie Radio) Atom feed")
    parser.add_argument("--full", action="store_true", help="Force full reset (ignore cache)")
    args = parser.parse_args()
    main(full_reset=args.full)
