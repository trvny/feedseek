"""TikTok feed: official Newsroom and public @tiktok videos.

Newsroom is parsed from dated official listing cards. Profile videos come from
public page hydration when available and the official embed as a fallback. One
blocked TikTok surface never prevents updating other sources.
"""

import argparse
import json
import re
import sys
from datetime import UTC, datetime
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from multi_rss import get_html, logger, parse_date, run
from utils import sanitize_xml

FEED_NAME = "tiktok"
NEWSROOM_URL = "https://newsroom.tiktok.com/?lang=en"
PROFILE_URL = "https://www.tiktok.com/@tiktok"
PROFILE_EMBED_URL = "https://www.tiktok.com/embed/@tiktok"

DATE_RE = re.compile(
    r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|"
    r"Dec(?:ember)?)\s+\d{1,2},?\s+20\d{2}\b",
    re.IGNORECASE,
)
VIDEO_ID_RE = re.compile(r"^\d{15,21}$")


def _parse_newsroom_listing(html):
    soup = BeautifulSoup(html or "", "html.parser")
    entries = []
    seen = set()

    for anchor in soup.find_all("a", href=True):
        link = urljoin(NEWSROOM_URL, anchor.get("href", ""))
        parsed = urlparse(link)
        if parsed.netloc != "newsroom.tiktok.com":
            continue
        path = parsed.path.rstrip("/")
        if not path or "-" not in path.rsplit("/", 1)[-1]:
            continue
        canonical = f"https://newsroom.tiktok.com{path}?lang=en"
        if canonical in seen:
            continue

        for card in [anchor, *list(anchor.parents)[:5]]:
            if card.name in {"main", "body", "html"}:
                break
            post_paths = {
                urlparse(urljoin(NEWSROOM_URL, a.get("href", ""))).path.rstrip("/")
                for a in card.find_all("a", href=True)
                if urlparse(urljoin(NEWSROOM_URL, a.get("href", ""))).netloc == "newsroom.tiktok.com"
                and "-" in urlparse(urljoin(NEWSROOM_URL, a.get("href", ""))).path.rsplit("/", 1)[-1]
            }
            if len(post_paths) > 1:
                break
            text = card.get_text(" ", strip=True)
            if len(text) > 4500:
                break
            match = DATE_RE.search(text)
            if not match:
                continue
            date_obj = parse_date(match.group(0))
            if date_obj is None:
                break

            heading = card.find(["h1", "h2", "h3", "h4"])
            title = heading.get_text(" ", strip=True) if heading else ""
            if not title:
                title = anchor.get_text(" ", strip=True)
            title = sanitize_xml(re.sub(r"\s+", " ", title).strip())
            if not title or title.casefold() in {"read", "read more", "learn more"}:
                break

            paragraph = card.find("p")
            description = (
                sanitize_xml(paragraph.get_text(" ", strip=True))[:500]
                if paragraph else title
            )
            entries.append({
                "title": title,
                "link": canonical,
                "date": date_obj,
                "description": description or title,
                "source": "TikTok Newsroom",
            })
            seen.add(canonical)
            break

    return entries


def scrape_newsroom(known_links):
    html = get_html(NEWSROOM_URL)
    if not html:
        return []
    candidates = _parse_newsroom_listing(html)
    if not candidates:
        logger.warning("  [TikTok Newsroom] no dated cards matched; layout may have changed")
    return [entry for entry in candidates if entry["link"] not in known_links]


def _profile_items(data):
    """Find video objects in either common TikTok hydration layout."""
    if isinstance(data, dict):
        modules = data.get("ItemModule")
        if isinstance(modules, dict):
            yield from (value for value in modules.values() if isinstance(value, dict))
        if (
            VIDEO_ID_RE.fullmatch(str(data.get("id") or ""))
            and data.get("createTime")
            and ("desc" in data or "video" in data)
        ):
            yield data
        for key, value in data.items():
            if key != "ItemModule" and isinstance(value, (dict, list)):
                yield from _profile_items(value)
    elif isinstance(data, list):
        for item in data:
            yield from _profile_items(item)


def _profile_entries(items):
    """Normalize official video metadata into stable feed entries."""
    entries = []
    seen = set()
    for item in items:
        video_id = str(item.get("id") or "")
        if not VIDEO_ID_RE.fullmatch(video_id) or video_id in seen:
            continue
        author = item.get("author")
        if isinstance(author, dict):
            author = author.get("uniqueId")
        if author and str(author).casefold().lstrip("@") != "tiktok":
            continue
        try:
            published = datetime.fromtimestamp(int(item["createTime"]), tz=UTC)
        except (ValueError, TypeError, OverflowError, KeyError):
            continue
        link = f"https://www.tiktok.com/@tiktok/video/{video_id}"
        description = str(item.get("desc") or "").strip()
        title = sanitize_xml(description)[:280] or f"TikTok video {video_id}"
        entries.append({
            "title": title,
            "link": link,
            "date": published,
            "description": sanitize_xml(description or title)[:500],
            "source": "TikTok @tiktok",
        })
        seen.add(video_id)
    return entries


def _parse_profile_html(html):
    soup = BeautifulSoup(html or "", "html.parser")
    items = []
    for script in soup.find_all(
        "script", id=["SIGI_STATE", "__UNIVERSAL_DATA_FOR_REHYDRATION__"]
    ):
        try:
            data = json.loads(script.string or script.get_text())
        except (ValueError, TypeError):
            continue
        items.extend(_profile_items(data))
    return _profile_entries(items)


def _parse_embed_profile_html(html):
    """Read TikTok's official creator embed state, without third-party RSS."""
    soup = BeautifulSoup(html or "", "html.parser")
    script = soup.find("script", id="__FRONTITY_CONNECT_STATE__")
    if script is None:
        return []
    try:
        state = json.loads(script.string or script.get_text())
    except (ValueError, TypeError):
        return []
    data = state.get("source", {}).get("data", {})
    if not isinstance(data, dict):
        return []

    items = []
    for profile in data.values():
        if not isinstance(profile, dict):
            continue
        user = profile.get("userInfo") or {}
        if not isinstance(user, dict) or str(user.get("uniqueId") or "").casefold() != "tiktok":
            continue
        for video in profile.get("videoList") or []:
            if not isinstance(video, dict):
                continue
            video_id = str(video.get("id") or "")
            if not VIDEO_ID_RE.fullmatch(video_id):
                continue
            items.append({
                "id": video_id,
                "author": video.get("authorUniqueId") or user["uniqueId"],
                "createTime": int(video_id) >> 32,
                "desc": video.get("desc") or "",
            })
    return _profile_entries(items)


def scrape_profile(known_links):
    html = get_html(PROFILE_URL)
    entries = _parse_profile_html(html) if html else []
    if not entries:
        embed_html = get_html(PROFILE_EMBED_URL)
        entries = _parse_embed_profile_html(embed_html) if embed_html else []
    if not entries:
        logger.warning("  [TikTok @tiktok] no public videos found; profile access may be blocked")
    return [entry for entry in entries if entry["link"] not in known_links]


def doc_sources():
    return [
        ("TikTok Newsroom", NEWSROOM_URL),
        ("TikTok @tiktok", PROFILE_URL),
    ]


def main(full=False):
    return run(
        feed_name=FEED_NAME,
        title="TikTok",
        subtitle="Official TikTok Newsroom articles and public @tiktok videos.",
        blog_url=NEWSROOM_URL,
        author="TikTok",
        extra_scrapers=(scrape_newsroom, scrape_profile),
        max_entries=200,
        per_source_cap=100,
        dedupe_title_field=None,
        full=full,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate the TikTok Atom feed")
    parser.add_argument("--full", action="store_true", help="Ignore cache and rebuild from scratch")
    sys.exit(0 if main(full=parser.parse_args().full) else 1)
