from datetime import UTC, datetime, timedelta

"""Gov.pl news feed generator.

Aggregates several Polish government news/announcement listings into one
**Atom** feed at ``feeds/feed_govpl_news.xml``. Sources (all gov.pl):

    - KPRM (Premier)            /web/premier/wydarzenia
    - Profil Zaufany           /web/profilzaufany/aktualnosci
    - Baza wiedzy              /web/baza-wiedzy/aktualnosci
    - Ministerstwo Cyfryzacji  /web/cyfryzacja/wiadomosci
    - Ministerstwo Zdrowia     /web/zdrowie/wiadomosci
    - Obrona Narodowa (MON)    /web/obrona-narodowa/aktualnosci5
    - Dyplomacja (MSZ)         /web/dyplomacja/aktualnosci
    - RCB (komunikaty)         /web/rcb/komunikaty
    - UOKiK                     uokik.gov.pl/feed (native RSS, PL + EN)
    - PARP                      parp.gov.pl news (native Joomla RSS)
    - Prezydent RP             prezydent.pl/aktualnosci (via Google News proxy)

parp.gov.pl's parpnewscom and publications components sit behind a JS/bot
challenge with no reachable feed, so PARP is pulled from the site's native
Joomla RSS (``?format=feed&type=rss``) instead -- on-domain article links,
real dates, news category. Its publications component has no feed equivalent.

gov.pl publishes no native feed. Every listing is server-rendered HTML sharing
one template: a ``.art-prev`` block of ``<li>`` items, each with a title, an
article link, and a DD.MM.YYYY date. So a single scraper handles all sources.

curl_cffi Chrome impersonation is used because gov.pl TLS-fingerprints plain
clients. The article lead (og:description) lives on the article page, so it is
fetched once per *new* link only. Listing dates refresh cached entries; cached
future dates get a bounded article-page recheck. Each source is wrapped so one
failure is skipped, never fatal.

prezydent.pl is the one exception: it sits behind a full Cloudflare *managed
challenge* (the "Just a moment..." JS interstitial), so it cannot be fetched
directly -- not even robots.txt, and not via the feeds-proxy worker. Its
``/aktualnosci`` content is instead pulled from the Google News RSS proxy
(``site:prezydent.pl``), same approach as ``reuters.py``. Tradeoff: links
point at Google News redirect URLs, and dates/leads come from the proxy. Its
``/kalendarz`` (a schedule of upcoming events, not articles) has no feed
equivalent and is intentionally not included.

(info.mobywatel.gov.pl was considered but excluded: a JS-rendered SPA with no
markup, no feed, and no API -- nothing to parse without a browser.)
"""

import argparse
from dataclasses import dataclass
import re
import sys
import time
from urllib.parse import urlsplit

from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from requests.exceptions import Timeout as RequestsTimeout
from enrich import enrich_entries
from feedgen.feed import FeedGenerator
from google_news import entry_url
from utils import (
    add_entry_media,
    deserialize_entries,
    favicon_proxy,
    feed_item_image,
    load_cache,
    merge_entries,
    sanitize_xml,
    save_atom_feed,
    save_cache,
    setup_feed_extensions,
    setup_feed_links,
    setup_logging,
    sort_posts_for_feed,
)

logger = setup_logging()

FEED_NAME = "govpl_news"
BLOG_URL = "https://www.gov.pl/"
BASE = "https://www.gov.pl"
MAX_ENTRIES = 150
MAX_DATE_RECHECKS = 5
MAX_FUTURE_DATE_SKEW = timedelta(days=1)

# label, listing URL
SOURCES = [
    ("KPRM", "https://www.gov.pl/web/premier/wydarzenia"),
    ("Profil Zaufany", "https://www.gov.pl/web/profilzaufany/aktualnosci"),
    ("Baza wiedzy", "https://www.gov.pl/web/baza-wiedzy/aktualnosci"),
    ("Min. Cyfryzacji", "https://www.gov.pl/web/cyfryzacja/wiadomosci"),
    ("Min. Zdrowia", "https://www.gov.pl/web/zdrowie/wiadomosci"),
    ("MON", "https://www.gov.pl/web/obrona-narodowa/aktualnosci5"),
    ("MSZ", "https://www.gov.pl/web/dyplomacja/aktualnosci"),
    ("RCB", "https://www.gov.pl/web/rcb/komunikaty"),
]

DATE_RE = re.compile(r"\b(\d{2}\.\d{2}\.\d{4})\b")
SLEEP_BETWEEN = 0.4

# Agencies that publish a real RSS feed -- parsed directly, no HTML scraping.
# (label, feed URL)
NATIVE_RSS = [
    ("UOKiK", "https://uokik.gov.pl/feed"),
    ("UOKiK (EN)", "https://uokik.gov.pl/en/feed"),
    ("PARP", "https://www.parp.gov.pl/?format=feed&type=rss"),
]

# prezydent.pl is behind a Cloudflare managed challenge -- unscrapeable. Pull its
# /aktualnosci posts from the Google News RSS proxy instead (links become GN
# redirects). `site:prezydent.pl` keeps results to the official site only.
PREZYDENT_GN_URL = (
    "https://news.google.com/rss/search?"
    "q=site:prezydent.pl&hl=pl&gl=PL&ceid=PL:pl"
)
PREZYDENT_SUFFIX_RE = re.compile(
    r"\s*[-\\|]\s*Oficjalna strona Prezydenta.*$", re.IGNORECASE
)
# prezydent.pl page titles tack on a "\ Aktualno\u015bci \ Wydarzenia" breadcrumb.
PREZYDENT_CRUMB_RE = re.compile(r"\s*\\+\s*(Aktualno\u015bci|Multimedia|Wydarzenia|Wideo|Galeria)\b.*$")


@dataclass
class GovplListingCircuit:
    """Per-refresh breaker for consecutive Gov.pl listing timeouts."""

    consecutive_timeouts: int = 0

    @property
    def stalled(self):
        """Only skip listings after two independent listing URLs time out."""
        return self.consecutive_timeouts >= 2

    def note_timeout(self):
        """Record a failed listing, not an article or date recheck."""
        self.consecutive_timeouts += 1
        if self.stalled:
            logger.warning("Gov.pl listing requests repeatedly timed out; skipping remaining Gov.pl listings")

    def note_success(self):
        """A reachable listing clears the consecutive failure count."""
        self.consecutive_timeouts = 0


def fetch_text(url, retries=3, backoff=2.0, *, timeout=30, on_exhausted_timeouts=None):
    """Fetch a page; report typed consecutive timeouts only when requested."""
    try:
        from curl_cffi import requests as creq
        from curl_cffi.requests.exceptions import Timeout as CurlTimeout
    except ImportError:
        creq = None
        CurlTimeout = RequestsTimeout

    # Google News answers Chrome-impersonated TLS with a 503 "Sorry" page.
    if url.startswith("https://news.google.com/"):
        creq = None
    timed_out = 0
    for attempt in range(1, retries + 1):
        try:
            if creq is not None:
                resp = creq.get(url, impersonate="chrome", timeout=timeout)
                resp.raise_for_status()
                return resp.text
            from utils import fetch_page
            return fetch_page(url, timeout=timeout)
        except (CurlTimeout, RequestsTimeout) as error:
            timed_out += 1
            logger.warning("Fetch timed out for %s (attempt %s/%s): %s", url, attempt, retries, error)
        except Exception as error:
            logger.warning("Fetch failed for %s (attempt %s/%s): %s", url, attempt, retries, error)
        if attempt < retries:
            time.sleep(backoff * attempt)
    if timed_out == retries and retries > 0 and on_exhausted_timeouts is not None:
        on_exhausted_timeouts()
    return None


def parse_date(date_str):
    """DD.MM.YYYY -> UTC datetime, or None."""
    if not date_str:
        return None
    try:
        dt = date_parser.parse(date_str, dayfirst=True)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)
    except (ValueError, TypeError, OverflowError):
        return None


def clean_description(text, fallback=""):
    if not text:
        return sanitize_xml(fallback)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > 500:
        text = text[:497].rstrip() + "..."
    return sanitize_xml(text or fallback)


def fetch_lead(url):
    """(og:description, og:image) for a new article; ("", None) if unavailable."""
    page = fetch_text(url, retries=2)
    if not page:
        return "", None
    s = BeautifulSoup(page, "html.parser")
    og = s.find("meta", property="og:description") or s.find("meta", attrs={"name": "description"})
    lead = og["content"].strip() if og and og.get("content") else ""
    img = s.find("meta", property="og:image") or s.find("meta", attrs={"name": "twitter:image"})
    image = img["content"].strip() if img and img.get("content") else None
    return lead, image


def collect_source(label, listing_url, cached_by_link, *, circuit=None):
    """Collect listing entries, tracking listing-only host timeout failures."""
    options = (
        {"retries": 2, "timeout": 15, "on_exhausted_timeouts": circuit.note_timeout}
        if circuit is not None else {}
    )
    html = fetch_text(listing_url, **options)
    if not html:
        logger.warning("[%s] fetch failed -- skipping this source", label)
        return []
    if circuit is not None:
        circuit.note_success()
    soup = BeautifulSoup(html, "html.parser")
    container = soup.select_one(".art-prev")
    if not container:
        logger.warning("[%s] no .art-prev block found -- structure may have changed", label)
        return []

    entries = []
    for li in container.select("li"):
        try:
            a = li.find("a", href=True)
            if not a:
                continue
            title = sanitize_xml(a.get_text(" ", strip=True))
            href = a["href"].split("?")[0].split("#")[0]
            if not title or not href:
                continue
            link = href if href.startswith("http") else BASE + href

            m = DATE_RE.search(li.get_text(" ", strip=True))
            date_obj = parse_date(m.group(1)) if m else None

            if link in cached_by_link:
                if date_obj is not None:
                    if cached_by_link[link].get("date") != date_obj:
                        logger.info("Refreshed cached publication date for %s: %s", link, date_obj)
                    cached_by_link[link]["date"] = date_obj
                continue
            lead, image = fetch_lead(link)
            description = clean_description(lead, fallback=title)
            time.sleep(SLEEP_BETWEEN)

            entries.append({
                "title": title,
                "link": link,
                "date": date_obj,
                "description": description,
                "source": label,
                "image": image,
            })
            logger.info("  [%s] %s", label, title)
        except Exception as e:
            logger.warning("[%s] skipped a malformed item: %s", label, e)
    logger.info("[%s] collected %d new entries", label, len(entries))
    return entries


def is_govpl_article(link):
    """Only first-party Gov.pl news pages use the suspicious-date quarantine."""
    try:
        target = urlsplit(link)
    except (TypeError, ValueError):
        return False
    return (target.scheme == "https" and target.netloc == "www.gov.pl"
            and target.path.startswith("/web/"))


def refresh_future_dates(cached, *, now=None):
    """Recheck suspicious cached dates against the article's publication field."""
    now = now or datetime.now(UTC)
    candidates = []
    for entry in cached:
        date = entry.get("date")
        if date is None or date <= now:
            continue
        link = entry.get("link", "")
        if not is_govpl_article(link):
            continue
        candidates.append(entry)
    if not candidates:
        return
    # Rotate each two-hour pipeline interval; persistent source errors cannot starve later entries.
    start = int(now.timestamp()) // 7200 % len(candidates)
    batch = (candidates[start:] + candidates[:start])[:MAX_DATE_RECHECKS]
    for entry in batch:
        link = entry["link"]
        try:
            page = fetch_text(link, retries=1)
            if not page:
                continue
            date_el = BeautifulSoup(page, "html.parser").select_one(".event-date")
            text = date_el.get_text(strip=True) if date_el else ""
            corrected = parse_date(text) if DATE_RE.fullmatch(text) else None
            if corrected is not None:
                if corrected != entry["date"]:
                    logger.info("Refreshed cached publication date for %s: %s", link, corrected)
                entry["date"] = corrected
        except Exception as error:
            logger.warning("Date recheck failed for %s: %s", link, error)


def collect_prezydent(known_links):
    """Pull prezydent.pl/aktualnosci posts from the Google News RSS proxy.

    Returns entries in the same shape as collect_source(). Links are Google
    News redirect URLs; titles have the " - Oficjalna strona Prezydenta..."
    source suffix stripped. Dates and leads come straight from the proxy, so
    no per-article fetch happens (the site can't be fetched anyway).
    """
    xml = fetch_text(PREZYDENT_GN_URL)
    if not xml:
        logger.warning("[Prezydent RP] Google News fetch failed -- skipping this source")
        return []
    soup = BeautifulSoup(xml, "xml")
    entries = []
    for item in soup.find_all("item"):
        try:
            title_el = item.find("title")
            link_el = item.find("link")
            if not title_el or not link_el:
                continue
            title = PREZYDENT_SUFFIX_RE.sub("", title_el.get_text(strip=True))
            title = PREZYDENT_CRUMB_RE.sub("", title)
            title = sanitize_xml(title.strip())
            link = link_el.get_text(strip=True)
            if not title or not link or link in known_links:
                continue
            date_el = item.find("pubDate")
            date_obj = None
            if date_el:
                try:
                    dt = date_parser.parse(date_el.get_text(strip=True))
                    date_obj = (dt if dt.tzinfo else dt.replace(tzinfo=UTC)).astimezone(UTC)
                except (ValueError, TypeError, OverflowError):
                    pass
            desc_el = item.find("description")
            raw_desc = desc_el.get_text(strip=True) if desc_el else ""
            description = clean_description(
                BeautifulSoup(raw_desc, "html.parser").get_text(" ", strip=True),
                fallback=title,
            )
            entries.append({
                "title": title,
                "link": link,
                "date": date_obj,
                "description": description,
                "source": "Prezydent RP",
                "image": feed_item_image(item),
            })
        except Exception as e:
            logger.warning("[Prezydent RP] skipped a malformed item: %s", e)
    logger.info("[Prezydent RP] collected %s new entries", len(entries))
    return entries


def collect_native_rss(label, url, known_links):
    """Parse a standard RSS feed (e.g. UOKiK) into the common entry shape."""
    xml = fetch_text(url)
    if not xml:
        logger.warning("[%s] RSS fetch failed -- skipping this source", label)
        return []
    soup = BeautifulSoup(xml, "xml")
    entries = []
    for item in soup.find_all("item"):
        try:
            title_el = item.find("title")
            link_el = item.find("link")
            if not title_el or not link_el:
                continue
            title = sanitize_xml(title_el.get_text(strip=True))
            link = (link_el.get_text(strip=True) or link_el.get("href") or "").strip()
            if not title or not link or link in known_links:
                continue
            date_el = item.find("pubDate") or item.find("published") or item.find("updated")
            date_obj = None
            if date_el:
                try:
                    dt = date_parser.parse(date_el.get_text(strip=True))
                    date_obj = (dt if dt.tzinfo else dt.replace(tzinfo=UTC)).astimezone(UTC)
                except (ValueError, TypeError, OverflowError):
                    pass
            desc_el = item.find("description") or item.find("summary") or item.find("content")
            description = clean_description(
                BeautifulSoup(desc_el.get_text() if desc_el else "", "html.parser").get_text(" ", strip=True),
                fallback=title,
            )
            entries.append({
                "title": title,
                "link": link,
                "date": date_obj,
                "description": description,
                "source": label,
                "image": feed_item_image(item),
            })
        except Exception as e:
            logger.warning("[%s] skipped a malformed item: %s", label, e)
    logger.info("[%s] collected %s new entries", label, len(entries))
    return entries


def collect_all(cached_by_link, *, circuit=None):
    """Collect all providers, skipping Gov.pl listings only after host failures."""
    circuit = circuit if circuit is not None else GovplListingCircuit()
    entries = []
    for label, url in SOURCES:
        if circuit.stalled:
            break
        logger.info("Scraping %s ...", label)
        try:
            entries += collect_source(label, url, cached_by_link, circuit=circuit)
        except Exception as e:
            logger.warning("[%s] unexpected error: %s", label, e)
    for label, url in NATIVE_RSS:
        logger.info("Fetching native RSS: %s ...", label)
        try:
            entries += collect_native_rss(label, url, cached_by_link)
        except Exception as e:
            logger.warning("[%s] unexpected error: %s", label, e)
    logger.info("Scraping Prezydent RP (Google News) ...")
    try:
        entries += collect_prezydent(cached_by_link)
    except Exception as e:
        logger.warning("[Prezydent RP] unexpected error: %s", e)
    return entries


def generate_atom_feed(articles, feed_name=FEED_NAME):
    fg = FeedGenerator()
    fg.id(f"{BLOG_URL}#{feed_name}")
    fg.title("Gov.pl")
    fg.subtitle("Wiadomosci i komunikaty z gov.pl -- KPRM, Cyfryzacja, Zdrowie, MON, MSZ, RCB, Profil Zaufany, Baza wiedzy, UOKiK, PARP -- oraz Prezydent RP, w jednym feedzie.")
    setup_feed_links(fg, BLOG_URL, feed_name, icon=favicon_proxy("gov.pl"))
    fg.language("pl")
    fg.author({"name": "gov.pl"})
    setup_feed_extensions(fg)

    for article in articles:
        fe = fg.add_entry()
        fe.id(article["link"])
        fe.title(article["title"])
        fe.link(href=entry_url(article))
        source = article.get("source")
        if source:
            fe.category(term=source, label=source)
        fe.description(article.get("description") or article["title"])
        if article.get("date"):
            fe.published(article["date"])
            fe.updated(article["date"])
        add_entry_media(fe, article.get("image"))
    logger.info("Generated Atom feed")
    return fg


def publishable_entries(articles, *, now=None):
    """Keep future-dated news in durable cache, not in published feeds."""
    cutoff = (now or datetime.now(UTC)) + MAX_FUTURE_DATE_SKEW
    publishable = []
    for article in articles:
        date = article.get("date")
        if date is not None and date > cutoff and is_govpl_article(article.get("link", "")):
            logger.warning("Deferring future-dated article %s (%s)", article.get("link"), date)
            continue
        publishable.append(article)
    return publishable


def main(full=False):
    """Refresh Gov.pl and independent sources, retaining prior good entries."""
    if full:
        logger.info("Full reset requested -- ignoring existing cache")
        cached = []
    else:
        cache = load_cache(FEED_NAME)
        cached = deserialize_entries(cache.get("entries", []), date_field="date")

    cached_by_link = {e["link"]: e for e in cached}
    circuit = GovplListingCircuit()
    new_articles = collect_all(cached_by_link, circuit=circuit)
    if not circuit.stalled:
        refresh_future_dates(cached)

    if not new_articles and not cached:
        logger.warning("No articles collected -- skipping write to avoid an empty feed")
        return False

    merged = merge_entries(new_articles, cached, id_field="link", date_field="date")
    merged = sort_posts_for_feed(merged, date_field="date")

    publishable = publishable_entries(merged)
    feed_items = publishable[-MAX_ENTRIES:] if len(publishable) > MAX_ENTRIES else publishable
    if not feed_items:
        save_cache(FEED_NAME, merged)
        logger.error("No publishable articles; refusing an empty feed")
        return False
    # Before the cache write: feed_items shares its dicts with merged, so the
    # resolved links and images are saved and never looked up again.
    # Separate image enrichment would otherwise retry the same stalled host.
    enrichable = (
        [e for e in feed_items if not e.get("link", "").startswith(("https://www.gov.pl/", "http://www.gov.pl/"))]
        if circuit.stalled else feed_items
    )
    if enrichable:
        enrich_entries(enrichable)
    save_cache(FEED_NAME, merged)
    save_atom_feed(generate_atom_feed(feed_items), FEED_NAME)
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate the Gov.pl Atom feed")
    parser.add_argument("--full", action="store_true", help="Ignore cache and rebuild from scratch")
    args = parser.parse_args()
    sys.exit(0 if main(full=args.full) else 1)
