from datetime import UTC

"""OpenAI feed generator.

Aggregates OpenAI's product/update sources into one **Atom** feed written to
``feeds/feed_openai.xml``:

    - OpenAI News            https://openai.com/news/rss.xml                    (native RSS)
    - OpenAI News PL         https://openai.com/pl-PL/news/                     (HTML)
    - OpenAI Research PL     https://openai.com/pl-PL/research/index/           (HTML)
    - OpenAI Engineering     https://openai.com/news/engineering/rss.xml        (native RSS)
    - OpenAI Release notes   https://openai.com/products/release-notes/rss.xml  (native RSS)
    - OpenAI Developers      https://developers.openai.com/rss.xml              (native RSS)
    - OpenAI Developer Blog  https://developers.openai.com/blog                 (HTML)
    - OpenAI Alignment       https://alignment.openai.com/                      (native RSS)
    - Misalignment reports   https://alignment.openai.com/misalignment-reports/  (HTML)
    - Deployment Safety      https://deploymentsafety.openai.com/                (HTML)
    - OpenAI Status          https://status.openai.com/feed.atom                 (native Atom)
    - Codex changelog        https://developers.openai.com/codex/changelog      (HTML)
    - Apps SDK changelog     https://developers.openai.com/apps-sdk/changelog   (HTML)
    - ChatGPT changelog      https://learn.chatgpt.com/docs/changelog           (HTML)
    - ChatGPT What's new     https://learn.chatgpt.com/docs/whats-new           (HTML)
    - ChatGPT release notes  https://help.openai.com/en/articles/6825453-chatgpt-release-notes (HTML)
    - API changelog          https://developers.openai.com/api/docs/changelog   (HTML)

Source handling:
  * RSS feeds — openai.com 403s plain requests (Cloudflare TLS fingerprinting),
    so everything is fetched via curl_cffi Chrome impersonation with a plain
    requests fallback. The News feed is huge (~1000 items), so per-run intake
    is capped to the newest slice; history still accumulates in the cache.
    English research posts are republished through the News RSS. The Polish
    News and Research indexes are scraped separately so localized titles and
    article links remain available without replacing the English entries.
  * Codex / Apps SDK changelogs — server-rendered Astro pages. Each entry is a
    ``<li id=...>`` with a ``<time>`` stamp, an ``<h3>`` title and an
    ``<article>`` body; the ``li`` id is a stable anchor, so links use it as a
    fragment (fragments are the only differentiator between entries — preserve
    them).
  * ChatGPT Help release notes — the Help Center article uses date ``<h1>``
    headings followed by one or more ``<h2>`` release titles. Synthetic
    fragments based on date + title provide stable per-entry links because the
    page itself does not expose durable entry anchors.
  * API changelog — entries are date-badged grid rows with no year and no
    anchors. The year is inferred by walking the (newest-first) list and
    rolling the year back whenever the month jumps upward; links get a
    synthetic ``#api-<date>-<slug>`` fragment for stable dedupe.

History accumulates across runs via the shared JSON cache
(``cache/openai_posts.json``); entries dedupe by link, then cross-source by
normalized URL/title (News and Engineering overlap).
"""

import argparse
import hashlib
import re
import sys
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from enrich import enrich_entries
from entry_identity import entry_id_for
from feedgen.feed import FeedGenerator
from utils import (
    add_entry_media,
    dedupe_entries,
    deserialize_entries,
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

FEED_NAME = "openai"
BLOG_URL = "https://openai.com/news/"
ALIGNMENT_URL = "https://alignment.openai.com/"
MISALIGNMENT_REPORTS_URL = "https://alignment.openai.com/misalignment-reports/"
DEPLOYMENT_SAFETY_URL = "https://deploymentsafety.openai.com/"
STATUS_ATOM_URL = "https://status.openai.com/feed.atom"
PL_NEWS_URL = "https://openai.com/pl-PL/news/"
PL_RESEARCH_URL = "https://openai.com/pl-PL/research/index/"
DEVELOPER_BLOG_URL = "https://developers.openai.com/blog"
CHATGPT_WHATS_NEW_URL = "https://learn.chatgpt.com/docs/whats-new"

# (label, rss_url, per-run intake cap or None)
RSS_SOURCES = [
    ("OpenAI News", "https://openai.com/news/rss.xml", 80),
    ("OpenAI Engineering", "https://openai.com/news/engineering/rss.xml", None),
    ("OpenAI Release notes", "https://openai.com/products/release-notes/rss.xml", 80),
    ("OpenAI Developers", "https://developers.openai.com/rss.xml", None),
    ("OpenAI Alignment", urljoin(ALIGNMENT_URL, "rss.xml"), 80),
    ("OpenAI Codex", "https://developers.openai.com/codex/changelog/rss.xml", None),
]

# (label, atom_url, per-run intake cap or None)
ATOM_SOURCES = [
    ("OpenAI Status", STATUS_ATOM_URL, 80),
]

# Scrape Research first so entries shared with News retain the more specific
# source label after link-level deduplication.
PL_INDEX_SOURCES = [
    ("OpenAI Research PL", PL_RESEARCH_URL),
    ("OpenAI News PL", PL_NEWS_URL),
]

# (label, page_url) — all share the li/time/h3/article layout.
LI_CHANGELOGS = [
    ("Codex changelog", "https://developers.openai.com/codex/changelog"),
    ("Apps SDK changelog", "https://developers.openai.com/apps-sdk/changelog"),
    ("ChatGPT changelog", "https://learn.chatgpt.com/docs/changelog"),
]

CHATGPT_HELP_LABEL = "ChatGPT release notes"
CHATGPT_HELP_URL = "https://help.openai.com/en/articles/6825453-chatgpt-release-notes"
CHATGPT_HELP_CAP = 80

API_CHANGELOG_LABEL = "API changelog"
API_CHANGELOG_URL = "https://developers.openai.com/api/docs/changelog"

MONTHS = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}
_BADGE_DATE_RE = re.compile(r"^([A-Z][a-z]{2})\s+(\d{1,2})$")
_HELP_DATE_RE = re.compile(
    r"^(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|"
    r"Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?,\s+\d{4}$",
    re.IGNORECASE,
)
_MISALIGNMENT_DATE_RE = re.compile(
    r"(?:Updated\s+|Notice\s*·\s*)([A-Z][a-z]{2,8}\s+\d{1,2},\s+\d{4})",
    re.IGNORECASE,
)
_SHORT_EN_DATE_RE = re.compile(
    r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})$"
)
_PL_DATE_RE = re.compile(
    r"^(\d{1,2})\s+"
    r"(sty(?:cznia)?|lut(?:ego)?|mar(?:ca)?|kwi(?:etnia)?|maj(?:a)?|"
    r"cze(?:rwca)?|lip(?:ca)?|sie(?:rpnia)?|wrz(?:eśnia)?|"
    r"paź(?:dziernika)?|lis(?:topada)?|gru(?:dnia)?)\s+(\d{4})$",
    re.IGNORECASE,
)
_WHATS_NEW_WEEK_RE = re.compile(
    r"^([A-Z][a-z]+)\s+(\d{1,2})\s*[–-]\s*"
    r"(?:(?P<end_month>[A-Z][a-z]+)\s+)?(?P<end_day>\d{1,2}),\s+(\d{4})$"
)

_PL_MONTHS = {
    "sty": 1, "stycznia": 1,
    "lut": 2, "lutego": 2,
    "mar": 3, "marca": 3,
    "kwi": 4, "kwietnia": 4,
    "maj": 5, "maja": 5,
    "cze": 6, "czerwca": 6,
    "lip": 7, "lipca": 7,
    "sie": 8, "sierpnia": 8,
    "wrz": 9, "września": 9,
    "paź": 10, "października": 10,
    "lis": 11, "listopada": 11,
    "gru": 12, "grudnia": 12,
}

DESC_LIMIT = 500
MAX_ENTRIES = 200


def _get_html(url):
    """Fetch a URL impersonating Chrome (openai.com 403s plain clients);
    fall back to plain requests if curl_cffi is unavailable. Returns text or None."""
    try:
        from curl_cffi import requests as creq

        resp = creq.get(url, impersonate="chrome", timeout=30)
    except ImportError:
        logger.warning(f"curl_cffi unavailable; using plain requests for {url}")
        try:
            resp = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0"},
                timeout=30,
            )
        except Exception as e:
            logger.warning(f"Fetch failed for {url}: {e}")
            return None
    except Exception as e:
        logger.warning(f"Fetch failed for {url}: {e}")
        return None
    if resp.status_code != 200:
        logger.warning(f"Fetch for {url} returned HTTP {resp.status_code}")
        return None
    return resp.text


def parse_date(date_str):
    """Parse a date string into a UTC datetime, or None on failure."""
    try:
        dt = date_parser.parse(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)
    except (ValueError, TypeError, OverflowError) as e:
        logger.warning(f"Could not parse date '{date_str}': {e}")
        return None


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")


def parse_pl_date(text):
    """Parse the Polish short/full month dates used on localized OpenAI indexes."""
    match = _PL_DATE_RE.match(re.sub(r"\s+", " ", text or "").strip())
    if not match:
        return None
    import datetime as _dt

    month = _PL_MONTHS[match.group(2).lower()]
    return _dt.datetime(int(match.group(3)), month, int(match.group(1)), tzinfo=UTC)


def parse_whats_new_week(text):
    """Return the end date of a ChatGPT What's new weekly range."""
    match = _WHATS_NEW_WEEK_RE.match(re.sub(r"\s+", " ", text or "").strip())
    if not match:
        return None
    import datetime as _dt

    start_month_name = match.group(1)
    end_month_name = match.group("end_month") or start_month_name
    try:
        end_month = date_parser.parse(end_month_name).month
    except (ValueError, TypeError, OverflowError):
        return None
    return _dt.datetime(
        int(match.group(5)), end_month, int(match.group("end_day")), tzinfo=UTC
    )


# --------------------------------------------------------------------------- #
# Native RSS feeds
# --------------------------------------------------------------------------- #


def scrape_rss(label, rss_url, known_links, cap=None):
    entries = []
    html = _get_html(rss_url)
    if html is None:
        return entries

    try:
        soup = BeautifulSoup(html, "xml")
    except Exception as e:
        logger.warning(f"Could not parse {rss_url}: {e}")
        return entries

    items = soup.find_all("item")
    if cap:
        items = items[:cap]
    for item in items:
        try:
            link_el = item.find("link")
            link = link_el.get_text(strip=True) if link_el else ""
            if not link or link in known_links:
                continue
            title_el = item.find("title")
            title = sanitize_xml(title_el.get_text(strip=True)) if title_el else label
            pub_el = item.find("pubDate")
            date_obj = parse_date(pub_el.get_text(strip=True)) if pub_el else None
            desc_el = item.find("description")
            if desc_el:
                desc = BeautifulSoup(desc_el.get_text(), "html.parser").get_text(" ", strip=True)
                desc = sanitize_xml(desc)[:DESC_LIMIT]
            else:
                desc = title
            entries.append({
                "title": title,
                "link": link,
                "date": date_obj,
                "description": desc or title,
                "source": label,
            })
            logger.info(f"  [{label}] {title}")
        except Exception as e:
            logger.warning(f"  [{label}] skipping malformed item: {e}")
    return entries


# --------------------------------------------------------------------------- #
# Atom feeds
# --------------------------------------------------------------------------- #


def scrape_atom(label, atom_url, known_links, cap=None):
    entries = []
    html = _get_html(atom_url)
    if html is None:
        return entries

    try:
        soup = BeautifulSoup(html, "xml")
    except Exception as e:
        logger.warning(f"Could not parse {atom_url}: {e}")
        return entries

    items = soup.find_all("entry")
    if cap:
        items = items[:cap]
    for item in items:
        try:
            link_el = item.find("link", href=True)
            link = link_el.get("href", "").strip() if link_el else ""
            if not link or link in known_links:
                continue
            title_el = item.find("title")
            title = sanitize_xml(title_el.get_text(" ", strip=True)) if title_el else label
            date_el = item.find("updated") or item.find("published")
            date_obj = parse_date(date_el.get_text(strip=True)) if date_el else None
            desc_el = item.find("content") or item.find("summary")
            if desc_el:
                desc_html = desc_el.get_text()
                desc = BeautifulSoup(desc_html, "html.parser").get_text(" ", strip=True)
                desc = sanitize_xml(desc)[:DESC_LIMIT]
            else:
                desc = title
            entries.append({
                "title": title,
                "link": link,
                "date": date_obj,
                "description": desc or title,
                "source": label,
            })
            logger.info(f"  [{label}] {title}")
        except Exception as e:
            logger.warning(f"  [{label}] skipping malformed entry: {e}")
    return entries


# --------------------------------------------------------------------------- #
# Localized OpenAI indexes / Developer Blog / ChatGPT What's new
# --------------------------------------------------------------------------- #


def _nearest_card(anchor):
    """Find a useful card-ish ancestor without depending on CSS class names."""
    for parent in anchor.parents:
        if getattr(parent, "name", None) in {"article", "li"}:
            return parent
        if getattr(parent, "name", None) == "main":
            break
    return anchor


def _first_heading(node):
    heading = node.find(["h2", "h3", "h4"]) if hasattr(node, "find") else None
    if heading:
        return re.sub(r"\s+", " ", heading.get_text(" ", strip=True))
    return ""


def _first_description(node, title):
    if not hasattr(node, "find_all"):
        return title
    for paragraph in node.find_all("p"):
        text = re.sub(r"\s+", " ", paragraph.get_text(" ", strip=True))
        if text and text != title:
            return sanitize_xml(text)[:DESC_LIMIT]
    return title


def _parse_pl_openai_index(html, label, page_url):
    soup = BeautifulSoup(html, "html.parser")
    entries = []
    seen_links = set()

    for anchor in soup.find_all("a", href=True):
        absolute = urljoin(page_url, anchor.get("href", ""))
        parsed = urlparse(absolute)
        if parsed.netloc != "openai.com":
            continue
        path = parsed.path
        if path.startswith("/pl-PL/index/"):
            localized_path = path
        elif path.startswith("/index/"):
            localized_path = "/pl-PL" + path
        else:
            continue
        if localized_path.rstrip("/") in {"/pl-PL/index", "/pl-PL/research/index"}:
            continue

        link = f"https://openai.com{localized_path}"
        if parsed.query:
            link += f"?{parsed.query}"
        if link in seen_links:
            continue

        card = _nearest_card(anchor)
        title = _first_heading(anchor) or _first_heading(card)
        strings = [
            re.sub(r"\s+", " ", text).strip()
            for text in anchor.stripped_strings
            if re.sub(r"\s+", " ", text).strip()
        ]
        if not title:
            title = next(
                (
                    text for text in strings
                    if len(text) >= 8 and parse_pl_date(text) is None
                ),
                "",
            )
        title = sanitize_xml(title)
        if not title:
            continue

        date_obj = None
        for node in (anchor, card):
            time_el = node.find("time") if hasattr(node, "find") else None
            if time_el:
                date_obj = parse_date(time_el.get("datetime") or time_el.get_text(" ", strip=True))
                if date_obj:
                    break
            for text in getattr(node, "stripped_strings", []):
                date_obj = parse_pl_date(text)
                if date_obj:
                    break
            if date_obj:
                break

        description = _first_description(anchor, title)
        if description == title:
            description = _first_description(card, title)

        entries.append({
            "title": title,
            "link": link,
            "date": date_obj,
            "description": description or title,
            "source": label,
        })
        seen_links.add(link)

    return entries


def scrape_pl_openai_index(label, page_url, known_links):
    html = _get_html(page_url)
    if html is None:
        return []
    entries = [
        entry for entry in _parse_pl_openai_index(html, label, page_url)
        if entry["link"] not in known_links
    ]
    if not entries and not known_links:
        logger.warning(f"  [{label}] no localized index entries matched — layout may have changed")
    for entry in entries:
        logger.info(f"  [{label}] {entry['title']}")
    return entries


def _parse_developer_blog_index(html, today=None):
    import datetime as _dt

    soup = BeautifulSoup(html, "html.parser")
    candidates = []
    seen_links = set()

    for anchor in soup.find_all("a", href=True):
        link = urljoin(DEVELOPER_BLOG_URL, anchor.get("href", ""))
        parsed = urlparse(link)
        if parsed.netloc != "developers.openai.com":
            continue
        path = parsed.path.rstrip("/")
        if not path.startswith("/blog/") or path.startswith("/blog/topic/"):
            continue
        if path == "/blog" or link in seen_links:
            continue

        strings = [
            re.sub(r"\s+", " ", text).strip()
            for text in anchor.stripped_strings
            if re.sub(r"\s+", " ", text).strip()
        ]
        date_match = None
        date_index = None
        for index, text in enumerate(strings):
            match = _SHORT_EN_DATE_RE.match(text)
            if match:
                date_match = match
                date_index = index
                break
        if not date_match:
            continue

        title = _first_heading(anchor)
        if not title and date_index is not None:
            title = next(
                (text for text in strings[date_index + 1:] if len(text) >= 4),
                "",
            )
        title = sanitize_xml(title)
        if not title:
            continue

        paragraph = anchor.find("p")
        description = (
            sanitize_xml(paragraph.get_text(" ", strip=True))[:DESC_LIMIT]
            if paragraph else title
        )
        candidates.append({
            "month": MONTHS[date_match.group(1)],
            "day": int(date_match.group(2)),
            "title": title,
            "link": link,
            "description": description or title,
        })
        seen_links.add(link)

    today = today or _dt.datetime.now(UTC)
    year = today.year
    prev_month = None
    entries = []
    for candidate in candidates:
        month = candidate["month"]
        day = candidate["day"]
        if prev_month is None:
            if (month, day) > (today.month, today.day + 7):
                year -= 1
        elif month > prev_month:
            year -= 1
        prev_month = month
        entries.append({
            "title": candidate["title"],
            "link": candidate["link"],
            "date": _dt.datetime(year, month, day, tzinfo=UTC),
            "description": candidate["description"],
            "source": "OpenAI Developer Blog",
        })

    return entries


def scrape_developer_blog(known_links):
    html = _get_html(DEVELOPER_BLOG_URL)
    if html is None:
        return []
    entries = [
        entry for entry in _parse_developer_blog_index(html)
        if entry["link"] not in known_links
    ]
    if not entries and not known_links:
        logger.warning("  [OpenAI Developer Blog] no posts matched — layout may have changed")
    for entry in entries:
        logger.info(f"  [OpenAI Developer Blog] {entry['title']}")
    return entries


def _whats_new_description(heading):
    parts = []
    seen = set()
    for node in heading.next_elements:
        name = getattr(node, "name", None)
        if name in {"h2", "h3"}:
            break
        if name not in {"p", "li"}:
            continue
        text = re.sub(r"\s+", " ", node.get_text(" ", strip=True))
        if not text or text in seen:
            continue
        seen.add(text)
        parts.append(text)
        if sum(len(part) for part in parts) >= DESC_LIMIT:
            break
    return sanitize_xml(" ".join(parts))[:DESC_LIMIT]


def _parse_chatgpt_whats_new(html):
    soup = BeautifulSoup(html, "html.parser")
    entries = []
    current_date = None

    for heading in soup.find_all(["h2", "h3"]):
        text = re.sub(r"\s+", " ", heading.get_text(" ", strip=True))
        if heading.name == "h2":
            current_date = parse_whats_new_week(text)
            continue
        if current_date is None or not text:
            continue

        title = sanitize_xml(text)
        title_hash = hashlib.sha256(title.encode("utf-8")).hexdigest()[:8]
        fragment = (
            f"whats-new-{current_date.date().isoformat()}-"
            f"{slugify(title)[:48]}-{title_hash}"
        )
        entries.append({
            "title": title,
            "link": f"{CHATGPT_WHATS_NEW_URL}#{fragment}",
            "date": current_date,
            "description": _whats_new_description(heading) or title,
            "source": "ChatGPT What's new",
        })

    return entries


def scrape_chatgpt_whats_new(known_links, cap=80):
    html = _get_html(CHATGPT_WHATS_NEW_URL)
    if html is None:
        return []
    candidates = _parse_chatgpt_whats_new(html)
    if cap:
        candidates = candidates[:cap]
    entries = [entry for entry in candidates if entry["link"] not in known_links]
    if not candidates:
        logger.warning("  [ChatGPT What's new] no weekly entries matched — layout may have changed")
    for entry in entries:
        logger.info(f"  [ChatGPT What's new] {entry['title']}")
    return entries


# --------------------------------------------------------------------------- #
# Alignment reports / Deployment Safety
# --------------------------------------------------------------------------- #


def _heading_block(heading):
    """Return text, paragraphs and links until the next h2/h3 heading."""
    title = re.sub(r"\s+", " ", heading.get_text(" ", strip=True))
    raw_parts = []
    paragraphs = []
    links = []
    seen_paragraphs = set()

    for node in heading.next_elements:
        name = getattr(node, "name", None)
        if name in {"h2", "h3"}:
            break
        if name == "a":
            href = node.get("href")
            if href:
                links.append(href)
        elif name == "p":
            text = re.sub(r"\s+", " ", node.get_text(" ", strip=True))
            if text and text != title and text not in seen_paragraphs:
                seen_paragraphs.add(text)
                paragraphs.append(text)
        elif name is None:
            text = re.sub(r"\s+", " ", str(node)).strip()
            if text and text != title:
                raw_parts.append(text)

    return " ".join(raw_parts), paragraphs, links


def _parse_misalignment_index(html):
    soup = BeautifulSoup(html, "html.parser")
    entries = []
    seen_links = set()

    for heading in soup.find_all("h3"):
        section = heading.find_previous("h2")
        section_name = section.get_text(" ", strip=True) if section else ""
        if section_name not in {"Reports", "Notices"}:
            continue

        title = sanitize_xml(re.sub(r"\s+", " ", heading.get_text(" ", strip=True)))
        block_text, paragraphs, links = _heading_block(heading)
        match = _MISALIGNMENT_DATE_RE.search(block_text)
        date_obj = parse_date(match.group(1)) if match else None

        if section_name == "Reports":
            link = None
            for href in links:
                absolute = urljoin(MISALIGNMENT_REPORTS_URL, href)
                if (
                    absolute.startswith(MISALIGNMENT_REPORTS_URL)
                    and absolute.rstrip("/") != MISALIGNMENT_REPORTS_URL.rstrip("/")
                ):
                    link = absolute
                    break
            if not link:
                continue
            source = "OpenAI Misalignment Report"
        else:
            date_slug = date_obj.date().isoformat() if date_obj else "undated"
            link = f"{MISALIGNMENT_REPORTS_URL}#notice-{slugify(title)}-{date_slug}"
            source = "OpenAI Misalignment Notice"

        if link in seen_links:
            continue
        seen_links.add(link)
        description = sanitize_xml(" ".join(paragraphs))[:DESC_LIMIT] or title
        entries.append({
            "title": title,
            "link": link,
            "date": date_obj,
            "description": description,
            "source": source,
        })

    return entries


def scrape_misalignment_reports(known_links):
    html = _get_html(MISALIGNMENT_REPORTS_URL)
    if html is None:
        return []
    entries = [
        entry for entry in _parse_misalignment_index(html)
        if entry["link"] not in known_links
    ]
    if not entries and not known_links:
        logger.warning("  [OpenAI Misalignment] no reports or notices matched — layout may have changed")
    for entry in entries:
        logger.info(f"  [{entry['source']}] {entry['title']}")
    return entries


def _parse_deployment_safety_index(html):
    soup = BeautifulSoup(html, "html.parser")
    entries = []
    seen_links = set()
    base_host = urlparse(DEPLOYMENT_SAFETY_URL).netloc

    for anchor in soup.find_all("a", href=True):
        link = urljoin(DEPLOYMENT_SAFETY_URL, anchor.get("href", ""))
        parsed = urlparse(link)
        if parsed.netloc != base_host or parsed.path in {"", "/"}:
            continue

        strings = [re.sub(r"\s+", " ", part).strip() for part in anchor.stripped_strings]
        strings = [part for part in strings if part]
        date_index = None
        date_obj = None
        for index, part in enumerate(strings):
            if _HELP_DATE_RE.match(part):
                date_index = index
                date_obj = parse_date(part)
                break
        if date_index is None or date_obj is None:
            continue

        heading = anchor.find(["h2", "h3", "h4"])
        title = (
            re.sub(r"\s+", " ", heading.get_text(" ", strip=True))
            if heading
            else next((part for part in strings[date_index + 1:] if part), "")
        )
        title = sanitize_xml(title)
        if not title or link in seen_links:
            continue

        paragraph = anchor.find("p")
        if paragraph:
            description = sanitize_xml(paragraph.get_text(" ", strip=True))[:DESC_LIMIT]
        else:
            tail = [part for part in strings[date_index + 1:] if part != title]
            description = sanitize_xml(" ".join(tail))[:DESC_LIMIT]
        entries.append({
            "title": title,
            "link": link,
            "date": date_obj,
            "description": description or title,
            "source": "OpenAI Deployment Safety",
        })
        seen_links.add(link)

    return entries


def scrape_deployment_safety(known_links):
    html = _get_html(DEPLOYMENT_SAFETY_URL)
    if html is None:
        return []
    entries = [
        entry for entry in _parse_deployment_safety_index(html)
        if entry["link"] not in known_links
    ]
    if not entries and not known_links:
        logger.warning("  [OpenAI Deployment Safety] no updates matched — layout may have changed")
    for entry in entries:
        logger.info(f"  [OpenAI Deployment Safety] {entry['title']}")
    return entries


# --------------------------------------------------------------------------- #
# Codex / Apps SDK changelogs (li id + time + h3 + article)
# --------------------------------------------------------------------------- #


def scrape_li_changelog(label, page_url, known_links):
    entries = []
    html = _get_html(page_url)
    if html is None:
        return entries
    soup = BeautifulSoup(html, "html.parser")

    items = soup.select("section[data-changelog-month-section] li[id]")
    if not items:
        logger.warning(f"  [{label}] no changelog entries matched — layout may have changed")
        return entries

    for li in items:
        try:
            anchor = li.get("id")
            link = f"{page_url}#{anchor}"
            if link in known_links:
                continue
            time_el = li.find("time")
            date_obj = parse_date(time_el.get_text(strip=True)) if time_el else None
            h3 = li.find("h3")
            # The h3 wraps the title span plus a copy-link button; take the span.
            span = h3.find("span") if h3 else None
            title_text = (span or h3).get_text(" ", strip=True) if h3 else anchor
            title = sanitize_xml(re.sub(r"\s+", " ", title_text))
            body_el = li.find("article")
            desc = body_el.get_text(" ", strip=True)[:DESC_LIMIT] if body_el else title
            entries.append({
                "title": title,
                "link": link,
                "date": date_obj,
                "description": sanitize_xml(desc) or title,
                "source": label,
            })
            logger.info(f"  [{label}] {title}")
        except Exception as e:
            logger.warning(f"  [{label}] skipping malformed item: {e}")
    return entries


# --------------------------------------------------------------------------- #
# ChatGPT Help Center release notes (h1 date -> h2 entries)
# --------------------------------------------------------------------------- #


def _help_entry_description(heading):
    """Collect body text after an entry heading until the next release heading."""
    parts = []
    seen = set()
    for node in heading.next_elements:
        name = getattr(node, "name", None)
        if name in {"h1", "h2"}:
            break
        if name not in {"p", "li"}:
            continue
        text = re.sub(r"\s+", " ", node.get_text(" ", strip=True))
        if not text or text in seen:
            continue
        seen.add(text)
        parts.append(text)
        if sum(len(part) for part in parts) >= DESC_LIMIT:
            break
    return sanitize_xml(" ".join(parts))[:DESC_LIMIT]


def scrape_chatgpt_help_release_notes(known_links, cap=CHATGPT_HELP_CAP):
    label = CHATGPT_HELP_LABEL
    entries = []
    html = _get_html(CHATGPT_HELP_URL)
    if html is None:
        return entries
    soup = BeautifulSoup(html, "html.parser")

    current_date = None
    matched_dates = 0
    matched_entries = 0
    for heading in soup.find_all(["h1", "h2"]):
        text = re.sub(r"\s+", " ", heading.get_text(" ", strip=True))
        if heading.name == "h1":
            if _HELP_DATE_RE.match(text):
                current_date = parse_date(text)
                if current_date is not None:
                    matched_dates += 1
            else:
                current_date = None
            continue
        if current_date is None or not text:
            continue

        # Cap the newest candidate slice before known-link filtering, matching
        # scrape_rss semantics and preventing gradual backfill of the whole
        # multi-year Help Center article on later runs.
        matched_entries += 1
        if cap and matched_entries > cap:
            break

        title = sanitize_xml(text)
        title_hash = hashlib.sha256(title.encode("utf-8")).hexdigest()[:8]
        fragment = (
            f"chatgpt-{current_date.date().isoformat()}-"
            f"{slugify(title)[:48]}-{title_hash}"
        )
        link = f"{CHATGPT_HELP_URL}#{fragment}"
        if link in known_links:
            continue
        description = _help_entry_description(heading) or title
        entries.append({
            "title": title,
            "link": link,
            "date": current_date,
            "description": description,
            "source": label,
        })
        logger.info(f"  [{label}] {title}")

    if not matched_dates:
        logger.warning(f"  [{label}] no dated sections matched — layout may have changed")
    elif not matched_entries:
        logger.warning(f"  [{label}] no release entries matched — layout may have changed")
    return entries


# --------------------------------------------------------------------------- #
# API changelog (date-badged grid rows; no year, no anchors)
# --------------------------------------------------------------------------- #


def scrape_api_changelog(known_links, today=None):
    import datetime as _dt

    label = API_CHANGELOG_LABEL
    entries = []
    html = _get_html(API_CHANGELOG_URL)
    if html is None:
        return entries
    soup = BeautifulSoup(html, "html.parser")

    rows = []
    for badge in soup.find_all("div", attrs={"data-variant": "outline"}):
        m = _BADGE_DATE_RE.match(badge.get_text(strip=True))
        if not m:
            continue
        row = badge.find_parent("div", class_=re.compile(r"grid"))
        if row is not None:
            rows.append((m.group(1), int(m.group(2)), row))
    if not rows:
        logger.warning(f"  [{label}] no changelog entries matched — layout may have changed")
        return entries

    # Rows are newest-first with no year on the badge. Anchor the first row to
    # the current year (stepping back one year if that lands in the future),
    # then roll the year back whenever the month jumps upward as we descend.
    today = today or _dt.datetime.now(UTC)
    year = today.year
    prev_month = None
    for mon_name, day, row in rows:
        try:
            month = MONTHS[mon_name]
            if prev_month is None:
                if (month, day) > (today.month, today.day + 7):
                    year -= 1
            elif month > prev_month:
                year -= 1
            prev_month = month
            date_obj = _dt.datetime(year, month, day, tzinfo=UTC)

            content = row.find("div", class_=re.compile(r"MarkdownContent"))
            text = content.get_text(" ", strip=True) if content else ""
            if not text:
                continue
            first_sentence = re.split(r"(?<=[.!?])\s", text, maxsplit=1)[0]
            tags = [
                b.get_text(strip=True)
                for b in row.find_all("div", attrs={"data-variant": "soft"})
            ]
            kind = tags[0] if tags else "Update"
            title = first_sentence if len(first_sentence) <= 110 else first_sentence[:107] + "..."
            title = sanitize_xml(f"{kind}: {title}")

            frag = f"api-{date_obj.date().isoformat()}-{slugify(' '.join(text.split()[:6]))[:48]}"
            link = f"{API_CHANGELOG_URL}#{frag}"
            if link in known_links:
                continue
            entries.append({
                "title": title,
                "link": link,
                "date": date_obj,
                "description": sanitize_xml(text)[:DESC_LIMIT] or title,
                "source": label,
            })
            logger.info(f"  [{label}] {title}")
        except Exception as e:
            logger.warning(f"  [{label}] skipping malformed item: {e}")
    return entries


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #


def scrape_all(known_links):
    new_entries = []
    for label, url, cap in RSS_SOURCES:
        logger.info(f"Scraping {label} ...")
        new_entries += scrape_rss(label, url, known_links, cap=cap)
    for label, url, cap in ATOM_SOURCES:
        logger.info(f"Scraping {label} ...")
        new_entries += scrape_atom(label, url, known_links, cap=cap)
    for label, url in PL_INDEX_SOURCES:
        logger.info(f"Scraping {label} ...")
        new_entries += scrape_pl_openai_index(label, url, known_links)
    logger.info("Scraping OpenAI Developer Blog ...")
    new_entries += scrape_developer_blog(known_links)
    logger.info("Scraping OpenAI Misalignment reports and notices ...")
    new_entries += scrape_misalignment_reports(known_links)
    logger.info("Scraping OpenAI Deployment Safety ...")
    new_entries += scrape_deployment_safety(known_links)
    for label, url in LI_CHANGELOGS:
        logger.info(f"Scraping {label} ...")
        new_entries += scrape_li_changelog(label, url, known_links)
    logger.info("Scraping ChatGPT What's new ...")
    new_entries += scrape_chatgpt_whats_new(known_links)
    logger.info(f"Scraping {CHATGPT_HELP_LABEL} ...")
    new_entries += scrape_chatgpt_help_release_notes(known_links)
    logger.info(f"Scraping {API_CHANGELOG_LABEL} ...")
    new_entries += scrape_api_changelog(known_links)
    return new_entries


def generate_atom_feed(articles, feed_name=FEED_NAME):
    fg = FeedGenerator()
    fg.id(f"https://openai.com/{feed_name}")
    fg.title("OpenAI")
    fg.subtitle(
        "OpenAI updates: News and Research (EN/PL), Engineering, Release notes, "
        "Developer Blog, Alignment, Deployment Safety, Status, ChatGPT, and changelogs."
    )
    setup_feed_links(fg, BLOG_URL, feed_name)
    setup_feed_extensions(fg)
    fg.language("en")
    fg.author({"name": "OpenAI"})

    for article in articles:
        fe = fg.add_entry()
        fe.id(entry_id_for(FEED_NAME, article))
        fe.title(article["title"])
        fe.link(href=article["link"])
        source = article.get("source")
        if source:
            fe.category(term=source, label=source)
        fe.description(article.get("description") or article["title"])
        add_entry_media(
            fe,
            article.get("image"),
            width=article.get("image_width"),
            height=article.get("image_height"),
        )
        if article.get("date"):
            fe.published(article["date"])
            fe.updated(article["date"])

    logger.info("Generated Atom feed")
    return fg


def main(full=False):
    if full:
        logger.info("Full reset requested — ignoring existing cache")
        cached = []
    else:
        cache = load_cache(FEED_NAME)
        cached = deserialize_entries(cache.get("entries", []), date_field="date")

    known_links = {e["link"] for e in cached}
    new_articles = scrape_all(known_links)

    if not new_articles and not cached:
        logger.warning("No articles collected — skipping write to avoid an empty feed")
        return False

    merged = merge_entries(new_articles, cached, id_field="link", date_field="date")
    merged = dedupe_entries(merged, id_field="link", title_field="title", date_field="date")
    merged = sort_posts_for_feed(merged, date_field="date")

    # Keep full (deduplicated) history in the cache so already-seen links are
    # never re-evaluated on later runs; only the rendered feed is capped.
    feed_items = merged[-MAX_ENTRIES:] if len(merged) > MAX_ENTRIES else merged
    # Before the cache write: feed_items shares its dicts with merged, so a
    # resolved image is saved and never looked up again.
    enrich_entries(feed_items)
    save_cache(FEED_NAME, merged)

    fg = generate_atom_feed(feed_items)
    save_atom_feed(fg, FEED_NAME)
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate the OpenAI Atom feed")
    parser.add_argument("--full", action="store_true", help="Ignore cache and rebuild from scratch")
    args = parser.parse_args()
    sys.exit(0 if main(full=args.full) else 1)