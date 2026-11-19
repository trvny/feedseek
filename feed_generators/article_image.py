"""Find an article's own image when the feed it came from shipped none.

Measured on 11.08.2026 across the 90 published feeds: **14 138 of 18 347
entries (77%) carried no image at all** - no media:content, no media:thumbnail,
no enclosure - so readers render them as a wall of text. 55 of the 82 worst
feeds run through :mod:`multi_rss`, and the reason is not that the pictures do
not exist: the upstream RSS simply omits them. The article page has the image
anyway, in the Open Graph tags every CMS emits so links look good on social
media. This module goes and gets it.

Cost is the whole design problem. The feeds regenerate every two hours, so a
naive "fetch every entry" pass would mean tens of thousands of requests a day
against other people's sites, for pictures that never change. Four things keep
it small:

- only entries about to be **published** are looked up, not everything cached;
- a hit is written into the entry, so the cache carries it forever after;
- a miss is remembered too (``image_checked``), so a genuinely imageless
  article is not re-fetched every run;
- each feed spends at most :data:`MAX_LOOKUPS` fetches and :data:`MAX_SECONDS`
  of wall clock per run, so the initial backfill spreads over runs instead of
  arriving as one thundering herd - and one unresponsive origin cannot push the
  scheduled job toward its timeout.

A network error is deliberately *not* recorded as a miss - it stays pending and
is retried next run, at most :data:`MAX_ATTEMPTS` times *per lookup URL*.
When a Google News wrapper URL fails transiently and later resolves to the real
article URL, the counter is bound to the wrapper, so the real URL is still
eligible for lookup. A 404 or 410 is recorded as a settled miss, because
that page is not coming back.
"""

from __future__ import annotations

import ipaddress
import json
import os
import queue
import re
import socket
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from concurrent.futures import TimeoutError as FuturesTimeout
from email.message import Message
from http.cookiejar import CookieJar
from threading import BoundedSemaphore, Thread
from urllib.parse import urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup, UnicodeDammit
from curl_cffi import CurlError, CurlOpt
from curl_cffi import requests as curl_requests
from feed_backends import extract_article_metadata
from utils import setup_logging

logger = setup_logging(__name__)

# Per-feed budget for one run. 40 x ~55 multi-source feeds is ~2200 fetches
# spread over a two-hourly job, and only until the backlog clears: once every
# published entry is resolved or marked, a normal run looks up only what is new.
MAX_LOOKUPS = int(os.environ.get("FEEDSEEK_IMAGE_LOOKUPS", "40"))
# Second budget, in wall clock. The scheduled job runs ~12 min against a 69 min
# timeout, and 55 feeds each waiting out a hung origin would eat that headroom;
# whatever a feed does not finish inside this stays pending for the next run.
MAX_SECONDS = float(os.environ.get("FEEDSEEK_IMAGE_SECONDS", "25"))
# Maximum number of attempts for a URL that keeps returning transient failures
# before marking it as permanently checked to avoid retrying it forever.
MAX_ATTEMPTS = int(os.environ.get("FEEDSEEK_IMAGE_ATTEMPTS", "3"))
WORKERS = 8
TIMEOUT = 10
MAX_REDIRECTS = 5
_DNS_SLOTS = BoundedSemaphore(WORKERS)
# Bound inspected HTML, including JSON-LD outside the head.
HEAD_BYTES = 262_144

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
}

# Ordered best-first. og:image is the near-universal one; the rest cover CMSes
# that emit a variant spelling, put the tag under name= instead of property=
# (technically wrong, widely done), or only ship Twitter cards.
_META_TAGS = (
    ("property", "og:image:secure_url"),
    ("property", "og:image"),
    ("name", "og:image"),
    ("property", "og:image:url"),
    ("name", "twitter:image"),
    ("property", "twitter:image"),
    ("name", "twitter:image:src"),
    ("itemprop", "image"),
)

# Sites that serve a house placeholder for every article are worse than no
# image: an identical picture on 200 entries reads as a rendering bug.
_JUNK_MARKERS = ("placeholder", "default-image", "no-image", "blank.gif", "spacer.gif")


def _absolute(url: object, base_url: str) -> str | None:
    """Absolutize a candidate, or reject it if it is not a usable http(s) image."""
    if not isinstance(url, str):
        return None
    url = url.strip()
    if not url or url.startswith("data:"):
        return None
    url = urljoin(base_url, url)
    if urlsplit(url).scheme not in ("http", "https"):
        return None
    if any(marker in url.lower() for marker in _JUNK_MARKERS):
        return None
    return url


def _from_json_ld(soup: BeautifulSoup, base_url: str) -> str | None:
    """Pull an image out of schema.org JSON-LD.

    Worth the trouble because news sites that omit Open Graph almost always
    still ship NewsArticle/BlogPosting metadata for Google. The ``image`` value
    is allowed to be a string, an ImageObject, or a list of either, and the
    payload may be a @graph wrapper, so this walks rather than indexes.
    """

    def walk(node):
        if isinstance(node, str):
            return node
        if isinstance(node, dict):
            # Only an ImageObject's own url is an image; an Article's url is the
            # article, and returning that would attach the page to itself.
            if node.get("@type") == "ImageObject" and isinstance(node.get("url"), str):
                return node["url"]
            for key in ("image", "thumbnailUrl", "primaryImageOfPage"):
                if key in node:
                    found = walk(node[key])
                    if found:
                        return found
            for key in ("@graph", "mainEntity", "mainEntityOfPage"):
                if key in node:
                    found = walk(node[key])
                    if found:
                        return found
            return None
        if isinstance(node, list):
            for item in node:
                found = walk(item)
                if found:
                    return found
        return None

    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = script.string or script.get_text()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except (ValueError, TypeError):
            continue  # hand-written JSON-LD is frequently invalid; skip it
        image = _absolute(walk(data), base_url)
        if image:
            return image
    return None


def _fast_page_image(html: str, base_url: str):
    """Fast path for declared image metadata; legacy handles other markup."""
    from selectolax.lexbor import LexborHTMLParser

    tree = LexborHTMLParser(html)

    def find_attr(attribute, value, key):
        node = tree.css_first(f'meta[{attribute}="{value}"]')
        return node.attributes.get(key) if node else None

    def dimension(prop):
        value = find_attr("property", prop, "content")
        try:
            size = int(value or 0)
        except (ValueError, TypeError):
            return None
        return size if 0 < size <= 10000 else None

    for attribute, value in _META_TAGS:
        image = _absolute(find_attr(attribute, value, "content"), base_url)
        if image:
            return image, dimension("og:image:width"), dimension("og:image:height")
    return None


def page_image(html: str, base_url: str) -> tuple[str | None, int | None, int | None]:
    """Best image URL declared by an HTML page, with dimensions when stated.

    Returns ``(url, width, height)``; width/height are ``None`` unless the page
    declares og:image:width / og:image:height. They are worth carrying: MRSS
    consumers that get them can lay out a thumbnail without downloading it
    first.
    """
    if not html:
        return None, None, None
    if os.environ.get("FEEDSEEK_HTML_PARSER") != "beautifulsoup":
        try:
            if result := _fast_page_image(html, base_url):
                return result
        except (ImportError, ValueError, RuntimeError) as exc:
            logger.debug("Selectolax image lookup fallback: %s", exc)
    soup = BeautifulSoup(html, "html.parser")

    image = None
    for attribute, value in _META_TAGS:
        element = soup.find("meta", attrs={attribute: value})
        if element:
            image = _absolute(element.get("content"), base_url)
            if image:
                break

    if not image:
        link = soup.find("link", rel="image_src")
        image = _absolute(link.get("href") if link else None, base_url)

    if not image:
        image = _from_json_ld(soup, base_url)

    if not image:
        # Same bounded HTML, no second network request. Only article markup.
        if soup.find("article") or soup.find("meta", property="og:type", content="article"):
            def candidate(metadata):
                url = _absolute(getattr(metadata, "image", None), base_url)
                return url if url and url != base_url and getattr(metadata, "title", None) else None

            image = extract_article_metadata(html, accept=candidate)
            if image:
                return image, None, None
        return None, None, None

    def dimension(prop: str) -> int | None:
        element = soup.find("meta", attrs={"property": prop})
        content = element.get("content") if element else None
        try:
            size = int(content.strip()) if isinstance(content, str) else 0
        except (ValueError, TypeError):
            return None
        return size if 0 < size <= 10000 else None

    return image, dimension("og:image:width"), dimension("og:image:height")


def _decode_html_prefix(body, headers) -> str:
    content_type = Message()
    content_type["Content-Type"] = headers.get("content-type", "")
    charset = content_type.get_content_charset()
    if charset:
        try:
            return body.decode(charset, errors="replace")
        except LookupError:
            pass
    return UnicodeDammit(body, is_html=True).unicode_markup or ""


def _public_address(address):
    ip = ipaddress.ip_address(address)
    if not ip.is_global or ip.is_multicast or ip.is_reserved:
        raise ValueError("non-public address")
    if isinstance(ip, ipaddress.IPv6Address) and (
        ip not in ipaddress.IPv6Network("2000::/3")
        or ip.sixtofour is not None
        or ip.teredo is not None
    ):
        raise ValueError("IPv6 translation or transition address")
    return ip


class _LookupDeferred(TimeoutError):
    """Local DNS capacity exhausted before a lookup could start."""


def _resolve_public_addresses(host, port, deadline):
    # getaddrinfo cannot be cancelled. Bound abandoned resolver threads globally;
    # daemon threads must not prolong process shutdown after the caller times out.
    slots = _DNS_SLOTS
    if deadline <= time.monotonic():
        raise TimeoutError("lookup deadline exhausted")
    if not slots.acquire(blocking=False):
        raise _LookupDeferred("DNS capacity exhausted")
    result = queue.Queue(maxsize=1)

    def resolve():
        try:
            records = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        except OSError as exc:
            records = exc
        finally:
            slots.release()
        result.put(records)

    try:
        Thread(target=resolve, daemon=True).start()
    except RuntimeError as exc:
        slots.release()
        raise OSError("DNS resolver could not start") from exc
    try:
        records = result.get(timeout=max(0, deadline - time.monotonic()))
    except queue.Empty as exc:
        raise TimeoutError("DNS lookup timed out") from exc
    if isinstance(records, OSError):
        raise records
    return dict.fromkeys(_public_address(record[4][0]) for record in records)


def _public_target(url: str, deadline=None):
    if deadline is None:
        deadline = time.monotonic() + TIMEOUT

    if any(ch.isspace() or ord(ch) < 32 or ord(ch) == 127 for ch in url) or "\\" in url:
        raise ValueError("invalid URL characters")
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise ValueError("expected HTTP(S) URL")
    if parts.username is not None or parts.password is not None or "%" in parts.netloc:
        raise ValueError("invalid authority")
    port = 443 if parts.scheme == "https" else 80
    if parts.port is not None and parts.port != port:
        raise ValueError("non-default port")
    host = parts.hostname.rstrip(".")
    options = {
        CurlOpt.PROXY: "",
        CurlOpt.PRE_PROXY: "",
        CurlOpt.PROTOCOLS_STR: "http,https",
        CurlOpt.FRESH_CONNECT: 1,
        CurlOpt.FORBID_REUSE: 1,
    }
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        literal = None
    if literal is None:
        host = host.encode("idna").decode("ascii").lower()
        # Reject alternate numeric address syntax before libcurl parses the URL.
        labels = host.split(".")
        if (
            len(host) > 253
            or len(labels) < 2
            or any(not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label) for label in labels)
            or re.fullmatch(r"(?:[0-9]+|0x[0-9a-f]+)", labels[-1])
        ):
            raise ValueError("invalid DNS hostname")
        addresses = _resolve_public_addresses(host, port, deadline)
        if not addresses:
            raise ValueError("no public DNS addresses")
        pinned = ",".join(f"[{ip}]" if ip.version == 6 else str(ip) for ip in addresses)
        options[CurlOpt.RESOLVE] = [f"{host}:{port}:{pinned}"]
        authority = host
    else:
        ip = _public_address(str(literal))
        authority = f"[{ip}]" if ip.version == 6 else str(ip)
    canonical = urlunsplit((parts.scheme, authority, parts.path or "/", parts.query, ""))
    return canonical, options


def _curl_prefix(url: str, options, timeout: float, *, impersonate: bool = False, cookies=None):
    from curl_cffi import CurlECode
    from curl_cffi.curl import CURL_WRITEFUNC_ERROR
    from curl_cffi.requests.exceptions import RequestException

    body = bytearray()
    capped = False

    def receive(chunk: bytes) -> int:
        nonlocal capped
        body.extend(chunk[:HEAD_BYTES - len(body)])
        if len(body) >= HEAD_BYTES:
            capped = True
            return CURL_WRITEFUNC_ERROR
        return len(chunk)

    complete = True
    try:
        # Fresh handle per hop; share only the domain-scoped cookie jar.
        with curl_requests.Session(
            cookies=cookies, trust_env=False, curl_options=options
        ) as session:
            response = session.get(
                url,
                headers=None if impersonate else HEADERS,
                impersonate="chrome" if impersonate else None,
                timeout=timeout,
                allow_redirects=False,
                content_callback=receive,
            )
    except RequestException as exc:
        response = exc.response
        if response is None or (response.status_code == 200 and not body):
            return None
        if not (capped and exc.code == CurlECode.WRITE_ERROR):
            if exc.code not in (
                CurlECode.OPERATION_TIMEDOUT,
                CurlECode.PARTIAL_FILE,
                CurlECode.RECV_ERROR,
            ):
                return None
        complete = False
    return response, bytes(body), complete and not capped


def _fetch_public_html(url: str, deadline, cookies, *, impersonate: bool = False):
    try:
        for _ in range(MAX_REDIRECTS + 1):
            url, options = _public_target(url, deadline)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None
            result = _curl_prefix(
                url, options, remaining, impersonate=impersonate, cookies=cookies
            )
            if result is None:
                return None
            response, body, complete = result
            if response.status_code in (301, 302, 303, 307, 308):
                location = response.headers.get("location")
                if not location:
                    return None
                url = urljoin(url, location)
                continue
            return url, response.status_code, response.headers, body, complete
    except _LookupDeferred:
        raise
    except (ValueError, OSError, CurlError) as exc:
        logger.debug("Public image lookup failed for %s: %s", url, exc)
    return None


def article_image(url: str, _session=None) -> tuple[str | None, int | None, int | None, bool]:
    """Fetch article metadata. A blocked or interrupted lookup stays retryable."""
    deadline = time.monotonic() + TIMEOUT
    cookies = CookieJar()
    result = _fetch_public_html(url, deadline, cookies)
    if result is None:
        return None, None, None, False
    url, status, headers, body, complete = result
    if status in (401, 403):
        # A slow denial body must not spend the browser retry's own budget.
        # At most two bounded chains; DNS and redirects share each chain's deadline.
        result = _fetch_public_html(
            url, time.monotonic() + TIMEOUT, cookies, impersonate=True
        )
        if result is None:
            return None, None, None, False
        url, status, headers, body, complete = result
    if status != 200:
        return None, None, None, status in (404, 410)
    content_type = (headers.get("content-type") or "").lower()
    if "html" not in content_type and content_type:
        return None, None, None, True
    image, width, height = page_image(_decode_html_prefix(body, headers), url)
    return image, width, height, bool(image) or complete


def backfill_images(
    entries: list[dict],
    *,
    limit: int = MAX_LOOKUPS,
    workers: int = WORKERS,
    max_seconds: float = MAX_SECONDS,
    lookup=article_image,
) -> int:
    """Fill in ``image`` for entries that have none. Returns how many were found.

    Mutates the entry dicts in place, which is the point: callers hand in the
    very dicts they are about to cache, so a resolved image is written once and
    read from the cache from then on. Newest entries are served first - they are
    what a reader actually sees when the budget runs out mid-backlog.
    """
    # article_url is set by google_news when the entry's link is a Google News
    # wrapper; asking the wrapper for a picture would always come back empty.
    def target(entry) -> str:
        return str(entry.get("article_url") or entry.get("link") or "")

    pending = [
        entry
        for entry in entries
        if not entry.get("image")
        and not entry.get("image_checked")
        and target(entry).startswith(("http://", "https://"))
        and not (
            entry.get("image_attempts", 0) >= MAX_ATTEMPTS
            and entry.get("image_attempt_url") == target(entry)
        )
    ]
    # Entries sharing one link have no per-article page to ask, so a lookup
    # would stamp the same picture on all of them - foobar2000 publishes 326
    # changelog entries across four URLs, and a reader seeing one image repeated
    # 326 times reads it as a rendering bug, not as illustration.
    #
    # Counted over every entry, not just the pending ones: whether a URL is
    # shared is a property of the feed, not of who still needs a picture.
    # Counting the filtered list instead would let the last unresolved sibling
    # look unique - the others having been resolved, marked or capped - and
    # collect the shared page's image after all.
    seen = Counter(
        target(entry)
        for entry in entries
        if target(entry).startswith(("http://", "https://"))
    )
    pending = [entry for entry in pending if seen[target(entry)] == 1]
    if not pending:
        return 0

    # entries arrive sorted ascending by date, so the tail is the newest.
    if limit is not None and limit <= 0:
        return 0  # a budget of zero means "not this run", not "no ceiling"
    batch = pending[-limit:] if limit and len(pending) > limit else pending
    logger.info(
        "Looking up images for %d of %d entries missing one", len(batch), len(pending)
    )

    pool = ThreadPoolExecutor(max_workers=workers)
    pending_futures = {pool.submit(lookup, target(entry), None): entry for entry in batch}

    def note_transient(entry) -> None:
        """Record one inconclusive attempt against the URL it was made on.

        Every way a lookup can end without an answer funnels through here -
        a transient status, a raised exception, or a future abandoned when the
        wall-clock budget expires. Missing any of them would exempt that whole
        class from the cap and leave it retried forever, which is the bug the
        cap exists to prevent.
        """
        url = target(entry)
        if entry.get("image_attempt_url") != url:
            entry["image_attempts"] = 0
        entry["image_attempts"] = entry.get("image_attempts", 0) + 1
        entry["image_attempt_url"] = url

    found = 0
    answered = 0
    handled: set[int] = set()
    try:
        for future in as_completed(pending_futures, timeout=max_seconds):
            entry = pending_futures[future]
            answered += 1
            handled.add(id(entry))
            try:
                image, width, height, settled = future.result()
            except _LookupDeferred:
                continue  # Local capacity, not a failed source attempt.
            except Exception as exc:  # a lookup must never sink the feed
                logger.debug("Image lookup raised for %s: %s", target(entry), exc)
                note_transient(entry)
                continue
            if image:
                entry["image"] = image
                if width:
                    entry["image_width"] = width
                if height:
                    entry["image_height"] = height
                found += 1
                # Clean up attempt tracking from prior failures
                entry.pop("image_attempts", None)
                entry.pop("image_attempt_url", None)
            elif settled:
                # A settled miss is final; mark it so it is not retried.
                entry["image_checked"] = True
            else:
                # Transient failure: retried at most MAX_ATTEMPTS times per URL.
                note_transient(entry)
    except FuturesTimeout:
        # An abandoned lookup is still an attempt, but only if it ever ran.
        # With 40 lookups over 8 workers most futures are still queued when the
        # budget expires; charging those an attempt would retire entries that
        # were never fetched at all. running() or done() is the difference
        # between an origin that hung and one we simply never got to.
        for future, entry in pending_futures.items():
            if id(entry) not in handled and (future.running() or future.done()):
                if future.done() and not future.cancelled() and isinstance(future.exception(), _LookupDeferred):
                    continue
                note_transient(entry)
        logger.info(
            "Image budget of %.0fs spent after %d of %d lookups; the rest waits for the next run",
            max_seconds,
            answered,
            len(batch),
        )
    finally:
        # Not waiting: whatever is still in flight has already had its answer
        # abandoned, and its own socket timeout ends it shortly after.
        pool.shutdown(wait=False, cancel_futures=True)

    logger.info("Resolved %d image(s); %d page(s) had none", found, answered - found)
    return found
