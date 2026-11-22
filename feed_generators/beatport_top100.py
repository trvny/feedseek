"""Beatport Top 100 feed generator.

Beatport blocks unattended requests with a Cloudflare managed challenge.
Try its former Next.js payload first; when blocked, use Soundcharts' public
weekly Beatport Global ranking. Only the first 95 tracks in that mirror
are public. Never substitute stale, incomplete, or obfuscated mirror data.

The chart is a *ranking* that changes over time, which doesn't map cleanly onto
a date-ordered feed. So instead of re-emitting the same 100 positions every run,
this generator treats the feed as **"tracks as they enter the Top 100"**: each
track becomes one Atom entry keyed by its verified source URL, dated by the
moment it is first observed on the chart, with the rank it debuted at
preserved in the summary. Mirror entries link to Soundcharts and disclose the
weekly chart date and attribution. The JSON cache (``cache/beatport_top100_posts.json``) accumulates history across
hourly runs and dedupes by track URL.

Writes an **Atom** feed to ``feeds/feed_beatport_top100.xml``.
"""

import argparse
import json
import re
import sys
import time
from datetime import UTC, datetime, timedelta
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from utils import (
    add_entry_media,
    deserialize_entries,
    favicon_proxy,
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

FEED_NAME = "beatport_top100"
BLOG_URL = "https://www.beatport.com/top-100"
TRACK_URL_TMPL = "https://www.beatport.com/track/{slug}/{id}"
MIRROR_URL = "https://soundcharts.com/en/charts/beatport/worldwide"
MIRROR_MIN_TRACKS = 90
DIRECT_MIN_TRACKS = 90
MIRROR_MAX_AGE_DAYS = 14
MIRROR_ID = re.compile(r"^/en/song/([0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})$")

# The chart accumulates over time; cap the committed XML at a sensible size.
MAX_ENTRIES = 200


def fetch_chart(retries=2, backoff=2.0):
    """Fetch the Top 100 HTML, returning the body or None.

    Beatport sits behind Cloudflare, which fingerprints the TLS handshake (JA3)
    and returns HTTP 403 to plain ``requests``/urllib3 even with browser-like
    headers. ``curl_cffi`` impersonates a real Chrome TLS fingerprint and gets
    through; we fall back to the shared ``fetch_page`` only if it isn't
    installed (which will likely 403, but keeps the import non-fatal).
    """
    try:
        from curl_cffi import requests as creq
    except ImportError:
        logger.warning("curl_cffi not installed; falling back to plain requests (likely 403)")
        from utils import fetch_page

        try:
            return fetch_page(BLOG_URL)
        except Exception as e:
            logger.error("Fallback fetch failed: %s", e)
            return None

    for attempt in range(1, retries + 1):
        try:
            resp = creq.get(BLOG_URL, impersonate="chrome", timeout=30)
            if resp.status_code == 200:
                if "__NEXT_DATA__" in resp.text:
                    logger.info("Fetched chart (%d bytes)", len(resp.text))
                    return resp.text
                logger.warning("Beatport HTML no longer exposes __NEXT_DATA__")
                break
            logger.warning("Beatport returned HTTP %d on attempt %d", resp.status_code, attempt)
            if resp.status_code in {401, 403}:
                break
        except Exception as e:
            logger.warning("Fetch failed (attempt %d/%d): %s", attempt, retries, e)
        if attempt < retries:
            time.sleep(backoff * attempt)
    return None


def extract_tracks(html):
    """Pull the 100-track results array out of the page's __NEXT_DATA__ blob."""
    soup = BeautifulSoup(html, "lxml")
    tag = soup.find("script", id="__NEXT_DATA__")
    if tag is None or not tag.string:
        logger.error("__NEXT_DATA__ script not found — page layout may have changed")
        return []
    try:
        data = json.loads(tag.string)
        queries = data["props"]["pageProps"]["dehydratedState"]["queries"]
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.error("Could not parse __NEXT_DATA__ structure: %s", e)
        return []

    for q in queries:
        results = (q.get("state", {}).get("data", {}) or {}).get("results")
        if isinstance(results, list) and results and isinstance(results[0], dict) and "mix_name" in results[0]:
            return results

    logger.error("Could not locate the track results array in __NEXT_DATA__")
    return []



def extract_mirror_tracks(html: str, now: datetime) -> list[dict]:
    """Read public weekly Beatport Global positions from Soundcharts.

    Only complete, fresh ranking prefixes qualify. The final five songs
    are paywalled placeholders, not valid track metadata.
    """
    soup = BeautifulSoup(html, "lxml")
    if "Beatport Charts - Global" not in soup.get_text(" ", strip=True):
        logger.warning("Soundcharts response is not the Beatport Global chart")
        return []

    week_match = re.search(
        r"Week of ([A-Za-z]+ [0-9]{1,2}, [0-9]{4})",
        soup.get_text(" ", strip=True),
    )
    if week_match is None:
        logger.warning("Soundcharts chart week missing")
        return []
    try:
        week = datetime.strptime(week_match.group(1), "%B %d, %Y").date()
    except ValueError:
        logger.warning("Soundcharts chart week is invalid")
        return []
    age = (now.date() - week).days
    if not -2 <= age <= MIRROR_MAX_AGE_DAYS:
        logger.warning("Soundcharts Beatport chart is stale or future-dated: %s", week)
        return []

    tracks = []
    seen_ids = set()
    for anchor in soup.select(".chart-panel__list a.rank[href^='/en/song/']"):
        match = MIRROR_ID.fullmatch(anchor.get("href", ""))
        rank_element = anchor.select_one(".rank__position")
        title_element = anchor.select_one(".rank__name")
        artist_element = anchor.select_one(".rank__artists")
        if not all((match, rank_element, title_element, artist_element)):
            continue
        title = title_element.get_text(" ", strip=True)
        artist = artist_element.get_text(" ", strip=True)
        if not title.strip("? ") or not artist.strip("? "):
            continue
        try:
            rank = int(rank_element.get_text(strip=True))
        except ValueError:
            continue
        uid = match.group(1)
        if uid in seen_ids:
            continue
        seen_ids.add(uid)
        image_element = anchor.select_one("img.rank__image")
        image = image_element.get("src", "") if image_element else ""
        if urlparse(image).netloc != "assets.soundcharts.com":
            image = ""
        tracks.append({
            "id": uid,
            "url": urljoin(MIRROR_URL, match.group(0)),
            "name": title,
            "artists": [{"name": artist}],
            "release": {"image": {"uri": image}} if image else {},
            "_mirror_week": week.isoformat(),
            "_rank": rank,
        })

    tracks.sort(key=lambda track: track["_rank"])
    positions = [track["_rank"] for track in tracks]
    if not (MIRROR_MIN_TRACKS <= len(tracks) <= 100):
        logger.warning("Soundcharts public ranking incomplete: %d tracks", len(tracks))
        return []
    if positions != list(range(1, len(tracks) + 1)):
        logger.warning("Soundcharts public ranking has gaps or duplicate positions")
        return []
    logger.info("Read %d Beatport Global tracks from Soundcharts, week of %s", len(tracks), week)
    return tracks


def fetch_mirror_tracks(now: datetime) -> list[dict]:
    """Fetch the public, non-paywalled chart; never follow arbitrary URLs."""
    try:
        response = requests.get(
            MIRROR_URL,
            timeout=15,
            headers={"User-Agent": "Feedseek/1.0 (Beatport chart feed)"},
        )
        response.raise_for_status()
        if len(response.content) > 2_000_000:
            logger.warning("Soundcharts HTML exceeds the 2 MiB budget")
            return []
        return extract_mirror_tracks(response.text, now)
    except requests.RequestException as exc:
        logger.warning("Soundcharts chart unavailable: %s", exc)
        return []


def build_entries(tracks, now):
    """Convert the raw chart tracks into feed-entry dicts.

    *now* is the first-seen timestamp applied to tracks seen in this run; the
    cache preserves the original timestamp for tracks already known, so the
    rank stored here is effectively each track's debut rank. Within a single
    run every track shares the same observation time, so we subtract the rank
    (in seconds) to keep the chart in order: higher-ranked tracks get the
    newer timestamp and therefore sort first in the feed.
    """
    entries = []
    seen_links = set()

    for rank, track in enumerate(tracks, start=1):
        try:
            entry_date = now - timedelta(seconds=rank)
            track_id = track.get("id")
            name = (track.get("name") or "").strip()
            if not track_id or not name:
                continue

            mirror_week = track.get("_mirror_week")
            slug = track.get("slug") or "track"
            link = (
                track["url"] if mirror_week
                else TRACK_URL_TMPL.format(slug=slug, id=track_id)
            )
            if link in seen_links:
                continue
            seen_links.add(link)

            mix = (track.get("mix_name") or "").strip()
            full_title = f"{name} ({mix})" if mix and mix.lower() != "original mix" else name

            artists = [a["name"] for a in track.get("artists", []) if a.get("name")]
            remixers = [r["name"] for r in track.get("remixers", []) if r.get("name")]
            artist_str = ", ".join(artists) or "Unknown Artist"

            release = track.get("release") or {}
            label = (release.get("label") or {}).get("name", "")
            genre = (track.get("genre") or {}).get("name", "")
            bpm = track.get("bpm")
            key = track.get("key")
            key_name = key.get("name") if isinstance(key, dict) else key
            length = track.get("length", "")

            title = sanitize_xml(f"{artist_str} - {full_title}")

            if mirror_week:
                bits = [
                    f"First seen at #{rank} in Soundcharts' weekly Beatport Global ranking",
                    f"Chart week: {mirror_week}",
                    "Source: Soundcharts public chart (95 of 100 tracks visible)",
                    f"Artists: {artist_str}",
                ]
            else:
                bits = [f"Entered the Beatport Top 100 at #{rank}", f"Artists: {artist_str}"]
            if remixers:
                bits.append(f"Remixers: {', '.join(remixers)}")
            if genre:
                bits.append(f"Genre: {genre}")
            if bpm:
                bits.append(f"BPM: {bpm}")
            if key_name:
                bits.append(f"Key: {key_name}")
            if length:
                bits.append(f"Length: {length}")
            if label:
                bits.append(f"Label: {label}")
            description = sanitize_xml(" · ".join(bits))

            entries.append(
                {
                    "title": title,
                    "link": link,
                    "date": entry_date,
                    "description": description,
                    "image": (release.get("image") or {}).get("uri"),
                }
            )
        except Exception as e:  # never let one bad track kill the run
            logger.warning("Skipping malformed track at rank %s: %s", rank, e)
            continue

    logger.info("Built %s entries from the chart", len(entries))
    return entries



def _recording_signature(title: str) -> tuple[tuple[str, ...], str] | None:
    """Strict artist+mix key for matching Beatport and Soundcharts records."""
    artist_text, separator, song = title.partition(" - ")
    if not separator or not artist_text or not song:
        return None
    artists = re.split(r",\s*|\s+&\s+", artist_text)
    artist_key = tuple(sorted(re.sub(r"\s+", " ", a.casefold()).strip() for a in artists))
    if not artist_key or any(not artist for artist in artist_key):
        return None
    song_key = re.sub(r"\s+", " ", song.casefold().replace("[", "(").replace("]", ")")).strip()
    song_key = re.sub(r"\s*\(original mix\)$", "", song_key).strip()
    return artist_key, song_key


def _source_provider(url: str) -> str | None:
    """Recognize only the two expected chart recording hosts."""
    host = urlparse(url).hostname
    if host in {"beatport.com", "www.beatport.com"}:
        return "beatport"
    if host == "soundcharts.com":
        return "soundcharts"
    return None


def _beatport_catalog_id(url: str) -> str | None:
    """Stable numeric Beatport track ID despite changing URL slugs."""
    if _source_provider(url) != "beatport":
        return None
    match = re.fullmatch(r"/track/[^/]+/([0-9]+)", urlparse(url).path)
    return match.group(1) if match else None


def _preserve_known_links(new_entries: list[dict], cached: list[dict]) -> None:
    """Reuse exact Beatport IDs, or unambiguous cross-provider recording keys."""
    cached_by_id: dict[str, list[dict]] = {}
    cached_by_signature: dict[tuple[tuple[str, ...], str], list[dict]] = {}
    new_by_signature: dict[tuple[tuple[str, ...], str], list[dict]] = {}
    for entry in cached:
        beatport_id = _beatport_catalog_id(entry.get("link", ""))
        if beatport_id:
            cached_by_id.setdefault(beatport_id, []).append(entry)
        sig = _recording_signature(entry.get("title") or "")
        if sig:
            cached_by_signature.setdefault(sig, []).append(entry)
    for entry in new_entries:
        beatport_id = _beatport_catalog_id(entry.get("link", ""))
        previous_id = cached_by_id.get(beatport_id, []) if beatport_id else []
        if len(previous_id) == 1:
            entry["link"] = previous_id[0]["link"]
            continue
        sig = _recording_signature(entry.get("title") or "")
        if sig:
            new_by_signature.setdefault(sig, []).append(entry)
    for sig, candidates in new_by_signature.items():
        previous = cached_by_signature.get(sig, [])
        if len(candidates) != 1 or len(previous) != 1:
            continue
        incoming, old = candidates[0], previous[0]
        old_provider = _source_provider(old.get("link", ""))
        new_provider = _source_provider(incoming.get("link", ""))
        if old_provider and new_provider and old_provider != new_provider:
            incoming["link"] = old["link"]


def generate_atom_feed(entries, feed_name=FEED_NAME, *, mirror=False):
    """Build an Atom FeedGenerator from the entry list."""
    fg = FeedGenerator()
    fg.id(f"https://www.beatport.com/{feed_name}")
    fg.title("Beatport Top 100")
    fg.subtitle(
        "New entrants in Soundcharts' weekly Beatport Global ranking (public top 95)"
        if mirror else "Tracks as they enter the Beatport Top 100 chart"
    )
    setup_feed_links(fg, BLOG_URL, feed_name, icon=favicon_proxy("beatport.com"))
    setup_feed_extensions(fg)
    fg.language("en")
    fg.author({"name": "Feedseek (Beatport chart)"})

    for entry in entries:
        fe = fg.add_entry()
        fe.id(entry["link"])
        fe.title(entry["title"])
        fe.link(href=entry["link"])
        publisher = (
            "Soundcharts (Beatport chart)" if urlparse(entry["link"]).netloc == "soundcharts.com"
            else "Beatport"
        )
        fe.author({"name": publisher})
        add_entry_media(fe, entry.get("image"))
        fe.description(entry["description"])
        if entry.get("date"):
            fe.published(entry["date"])
            fe.updated(entry["date"])

    logger.info("Generated Atom feed")
    return fg


def main(full=False):
    """Fetch the chart, merge with cache, and write the Atom feed."""
    now = datetime.now(UTC)
    html = fetch_chart()
    tracks = extract_tracks(html) if html else []
    new_entries = build_entries(tracks, now) if tracks else []
    mirror = len(new_entries) < DIRECT_MIN_TRACKS
    if mirror:
        logger.warning("Beatport direct chart unusable; checking the public weekly mirror")
        tracks = fetch_mirror_tracks(now)
        new_entries = build_entries(tracks, now) if tracks else []
    if len(new_entries) < MIRROR_MIN_TRACKS:
        logger.error("Neither the Beatport chart nor a fresh complete mirror is available")
        return False

    if full:
        logger.info("Full reset requested — ignoring existing cache")
        cached = []
    else:
        cache = load_cache(FEED_NAME)
        cached = deserialize_entries(cache.get("entries", []), date_field="date")

    # Reuse old links only when artists, title and mix identify one prior track.
    # merge_entries then keeps its original first-seen date and Atom identity.
    _preserve_known_links(new_entries, cached)
    merged = merge_entries(new_entries, cached, id_field="link", date_field="date")
    merged = sort_posts_for_feed(merged, date_field="date")

    # sort_posts_for_feed returns ascending (feedgen reverses on write), so keep
    # the tail to retain the most recently charted tracks.
    if len(merged) > MAX_ENTRIES:
        merged = merged[-MAX_ENTRIES:]

    save_cache(FEED_NAME, merged)

    fg = generate_atom_feed(merged, mirror=mirror)
    save_atom_feed(fg, FEED_NAME)
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate the Beatport Top 100 Atom feed")
    parser.add_argument("--full", action="store_true", help="Ignore cache and rebuild from scratch")
    args = parser.parse_args()
    sys.exit(0 if main(full=args.full) else 1)
