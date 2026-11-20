"""Compare candidate libraries on bounded public Feedseek and upstream inputs."""
import argparse
import asyncio
import gzip
import hashlib
import importlib
import json
import statistics
import sys
import tempfile
import time
from collections import Counter
from importlib.metadata import version
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urljoin, urlsplit

import aiohttp

PAGES = "https://trvny.github.io/feedseek/"
FEEDS = [PAGES + key + ".xml" for key in (
    "jbzd", "beatport_top100", "openai", "github", "weather",
    "reuters", "arxiv", "wikipedia_pl",
)] + ["https://github.blog/feed/", "https://blog.python.org/rss.xml",
      "https://www.independent.co.uk/rss", "https://www.indy100.com/feeds/feed.rss"]
SITES = ["https://www.independent.co.uk/", "https://www.indy100.com/",
         "https://github.blog/", "https://www.python.org/", "https://xkcd.com/"]
FIELDS = ("id", "title", "link", "published", "updated", "summary",
          "content", "author", "tags", "media_content", "enclosures")
MAX_BYTES = 8 * 1024 * 1024
BENCHMARK_HOSTS = {
    "trvny.github.io", "github.blog", "www.independent.co.uk", "www.indy100.com",
    "www.python.org", "blog.python.org", "peps.python.org", "pyfound.blogspot.com",
    "xkcd.com", "www.xkcd.com",
}


def validate_url(url):
    parts = urlsplit(url)
    if (parts.scheme != "https" or parts.hostname not in BENCHMARK_HOSTS
            or parts.username or parts.password or parts.port not in (None, 443)):
        raise ValueError("URL outside benchmark hosts")


async def download_async(url, deadline):
    # Total timeout includes DNS, headers and body, including slow streams.
    async with aiohttp.ClientSession(
        headers={"User-Agent": "Feedseek benchmark/1.0"}
    ) as session:
        for _ in range(5):
            validate_url(url)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("benchmark deadline reached")
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=remaining), allow_redirects=False
            ) as response:
                if response.status in (301, 302, 303, 307, 308):
                    location = response.headers.get("Location")
                    if not location:
                        raise ValueError(f"redirect without Location: {url}")
                    url = urljoin(url, location)
                    continue
                response.raise_for_status()
                body = bytearray()
                async for chunk in response.content.iter_chunked(65536):
                    if len(body) + len(chunk) > MAX_BYTES:
                        raise ValueError("response too large")
                    body.extend(chunk)
                return bytes(body)
    raise ValueError("too many redirects")


def download(url, *, deadline=None, timeout=15):
    request_deadline = time.monotonic() + timeout
    deadline = request_deadline if deadline is None else min(deadline, request_deadline)
    data = asyncio.run(download_async(url, deadline))
    if data.startswith(b"\x1f\x8b"):
        with gzip.GzipFile(fileobj=BytesIO(data)) as compressed:
            data = compressed.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError("decompressed response too large")
    return data


def fingerprint(value):
    return hashlib.sha256(str(value or "").encode("utf-8")).hexdigest()


def timed(fn):
    result = fn()
    durations = []
    for _ in range(5):
        start = time.perf_counter()
        fn()
        durations.append(time.perf_counter() - start)
    return result, round(statistics.median(durations) * 1000, 3)


def value(entry, key):
    try:
        return entry[key]
    except (KeyError, TypeError, AttributeError):
        return getattr(entry, key, None)


def coverage(entries):
    return {key: sum(bool(value(entry, key)) for entry in entries) for key in FIELDS}


def identities(entries):
    return Counter(str(value(entry, "link")) for entry in entries if value(entry, "link"))


def emit(**row):
    print(json.dumps(row, ensure_ascii=True, default=str), flush=True)


def compare_projection(data, candidate, url):
    """Compare actual Model Feed fields, without printing content."""
    from model_feed import build_model_feed
    from jsonfeed import build_json_feed
    from utils import feedparser_entry_image

    key = Path(urlsplit(url).path).stem
    with tempfile.TemporaryDirectory() as directory:
        xml = Path(directory) / "feed.xml"
        xml.write_bytes(data)

        def project():
            return build_model_feed(build_json_feed(xml, key, feedparser_entry_image), key)

        baseline = project()
        with patch("feedparser.parse", candidate.parse):
            result = project()
    # Compare the whole document, including field values and list ordering.
    a, b = baseline.get("items", []), result.get("items", [])
    differences = {}
    for old, new in zip(a, b):
        for field in old.keys() | new.keys():
            if old.get(field) != new.get(field):
                differences[field] = differences.get(field, 0) + 1
    emit(url=url, model_exact=baseline == result, model_baseline_count=len(a),
         model_candidate_count=len(b), model_item_field_differences=differences,
         model_top_level_differences=sorted(
             field for field in baseline.keys() | result.keys()
             if field != "items" and baseline.get(field) != result.get(field)
         ))


def check_parser(package, url):
    import feedparser

    candidate = importlib.import_module(package.replace("-", "_"))
    data = download(url)
    base, base_ms = timed(lambda: feedparser.parse(data))
    other, other_ms = timed(lambda: candidate.parse(data))
    a, b = list(base.entries), list(other.entries)
    emit(url=url, bytes=len(data), baseline_ms=base_ms, candidate_ms=other_ms,
         baseline_entries=len(a), candidate_entries=len(b),
         missing_links=sum((identities(a) - identities(b)).values()),
         extra_links=sum((identities(b) - identities(a)).values()),
         item_ids_exact=[value(e, "id") for e in a] == [value(e, "id") for e in b],
         baseline_coverage=coverage(a), candidate_coverage=coverage(b),
         baseline_bozo=value(base, "bozo"), candidate_bozo=value(other, "bozo"))
    if package == "feedparser-rs" and url.startswith(PAGES):
        compare_projection(data, candidate, url)


def check_html(url):
    from bs4 import BeautifulSoup
    from selectolax.lexbor import LexborHTMLParser

    html = download(url).decode("utf-8", errors="replace")

    def select_bs(backend):
        return [(n.get("href"), n.get_text(" ", strip=True))
                for n in BeautifulSoup(html, backend).select("a[href]")]

    def select_lexbor():
        return [(n.attributes.get("href"), n.text(separator=" ", strip=True))
                for n in LexborHTMLParser(html).css("a[href]")]

    for backend in ("html.parser", "lxml"):
        a, base_ms = timed(lambda: select_bs(backend))
        b, other_ms = timed(select_lexbor)
        emit(url=url, baseline=backend, baseline_ms=base_ms, candidate_ms=other_ms,
             baseline_links=len(a), candidate_links=len(b),
             missing_links=sum((Counter(x[0] for x in a) - Counter(x[0] for x in b)).values()),
             extra_links=sum((Counter(x[0] for x in b) - Counter(x[0] for x in a)).values()),
             missing_link_text_pairs=sum((Counter(a) - Counter(b)).values()),
             extra_link_text_pairs=sum((Counter(b) - Counter(a)).values()),
             exact_order=a == b)


def check_article(package, url):
    candidate = importlib.import_module(package)
    data = download(url)
    html = data.decode("utf-8", errors="replace")
    doc, ms = timed(lambda: candidate.bare_extraction(html, url=url))
    meta, metadata_ms = timed(lambda: candidate.extract_metadata(html))
    emit(url=url, candidate_ms=ms, text_chars=len(getattr(doc, "text", "") or ""),
         metadata_ms=metadata_ms,
         input_sha256=hashlib.sha256(data).hexdigest(),
         text_sha256=fingerprint(getattr(doc, "text", None)),
         metadata_sha256={field: fingerprint(getattr(meta, field, None))
                          for field in ("title", "author", "date", "image")},
         has_title=bool(getattr(meta, "title", None)),
         has_author=bool(getattr(meta, "author", None)),
         has_date=bool(getattr(meta, "date", None)),
         has_image=bool(getattr(meta, "image", None)))


def check_discovery(package, url):
    import feedparser

    start = time.perf_counter()
    if package == "feed-seeker":
        from feed_seeker import FeedSeeker

        deadline = start + 12

        def fetch(candidate):
            try:
                return download(candidate, deadline=deadline, timeout=4).decode("utf-8", errors="replace")
            except TimeoutError:
                if time.monotonic() >= deadline:
                    raise
                return ""
            except (aiohttp.ClientError, ValueError, gzip.BadGzipFile, EOFError):
                return ""

        found = []
        try:
            for link in FeedSeeker(url, fetcher=fetch).generate_feed_urls(max_links=40):
                if link not in found:
                    found.append(link)
                if len(found) >= 15 or time.monotonic() >= deadline:
                    break
        except TimeoutError:
            pass  # Preserve validated results from the completed probes.
    else:
        from feedsearch_crawler import search_with_info

        # Crawler owns its transport. Apply the allowlist to starts AND redirects.
        trace = aiohttp.TraceConfig()

        async def check_start(_session, _context, params):
            validate_url(str(params.url))

        async def check_redirect(_session, _context, params):
            location = params.response.headers.get("Location") or params.response.headers.get("URI")
            if location:
                validate_url(urljoin(str(params.url), location))

        trace.on_request_start.append(check_start)
        trace.on_request_redirect.append(check_redirect)
        original_session = aiohttp.ClientSession

        def bounded_session(*args, **kwargs):
            kwargs["trace_configs"] = [*(kwargs.get("trace_configs") or []), trace]
            return original_session(*args, **kwargs)

        with patch("aiohttp.ClientSession", side_effect=bounded_session):
            result = search_with_info(
                url, total_timeout=12, request_timeout=4, favicon_data_uri=False,
                allowed_domains=sorted(BENCHMARK_HOSTS), allowed_schemes=["https"],
                max_content_length=MAX_BYTES, ssl=True,
            )
        if result.root_error and not result.feeds:
            raise ValueError(result.root_error.message)
        found = [str(feed.url) for feed in result.feeds[:15]]
    elapsed = round(time.perf_counter() - start, 3)
    found = list(dict.fromkeys(map(str, found)))
    verified = []
    for link in found[:5]:
        try:
            parsed = feedparser.parse(download(link))
            if parsed.version and parsed.entries:
                verified.append(link)
        except (aiohttp.ClientError, OSError, ValueError, EOFError) as exc:
            emit(url=link, verification_error=str(exc)[:300])
    emit(url=url, discovery_seconds=elapsed, candidates=found, verified_nonempty=verified)


def article_urls():
    import feedparser

    for feed in ("https://github.blog/feed/", "https://blog.python.org/rss.xml"):
        try:
            for entry in feedparser.parse(download(feed)).entries[:2]:
                yield entry.link
        except Exception as exc:
            emit(url=feed, error=str(exc)[:300])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", choices=[
        "fastfeedparser", "feedparser-rs", "selectolax", "trafilatura",
        "rtrafilatura", "feed-seeker", "feedsearch-crawler",
    ])
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))
    package = parser.parse_args().package
    emit(candidate=package, version=version(package), baselines={
        name: version(name) for name in ("feedparser", "beautifulsoup4", "lxml", "aiohttp", "feedgen2", "requests")
    })
    urls = FEEDS if package in {"fastfeedparser", "feedparser-rs"} else SITES
    if package in {"trafilatura", "rtrafilatura"}:
        urls = list(article_urls())
    successes = 0
    required_failures = 0
    for url in urls:
        try:
            if package in {"fastfeedparser", "feedparser-rs"}:
                check_parser(package, url)
            elif package == "selectolax":
                check_html(url)
            elif package in {"trafilatura", "rtrafilatura"}:
                check_article(package, url)
            else:
                check_discovery(package, url)
            successes += 1
        except Exception as exc:
            emit(url=url, error=str(exc)[:300])
            if package == "feedparser-rs" and url.startswith(PAGES):
                required_failures += 1
    emit(successful_comparisons=successes, required_failures=required_failures, attempted=len(urls))
    if not successes or required_failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
