"""Compare candidate libraries on bounded public Feedseek and upstream inputs."""
import argparse
import gzip
import importlib
import itertools
import json
import statistics
import sys
import tempfile
import time
from importlib.metadata import version
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urljoin, urlsplit

import requests

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


def download(url):
    # Known benchmark hosts only, including redirects and discovered candidates.
    for _ in range(5):
        parts = urlsplit(url)
        if (parts.scheme != "https" or parts.hostname not in BENCHMARK_HOSTS
                or parts.username or parts.password or parts.port not in (None, 443)):
            raise ValueError("URL outside benchmark hosts")
        with requests.get(url, headers={"User-Agent": "Feedseek benchmark/1.0"},
                          stream=True, timeout=15, allow_redirects=False) as response:
            if response.is_redirect:
                url = urljoin(url, response.headers["Location"])
                continue
            response.raise_for_status()
            body = bytearray()
            for chunk in response.iter_content(65536):
                body.extend(chunk)
                if len(body) > MAX_BYTES:
                    raise ValueError("response too large")
            data = bytes(body)
            break
    else:
        raise ValueError("too many redirects")
    if data.startswith(b"\x1f\x8b"):
        with gzip.GzipFile(fileobj=BytesIO(data)) as compressed:
            data = compressed.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError("decompressed response too large")
    return data


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
    return {str(value(entry, "link")) for entry in entries if value(entry, "link")}


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
         missing_links=len(identities(a) - identities(b)),
         extra_links=len(identities(b) - identities(a)),
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
             missing_links=len({x[0] for x in a} - {x[0] for x in b}),
             extra_links=len({x[0] for x in b} - {x[0] for x in a}))


def check_article(package, url):
    candidate = importlib.import_module(package)
    html = download(url).decode("utf-8", errors="replace")
    doc, ms = timed(lambda: candidate.bare_extraction(html, url=url))
    meta, metadata_ms = timed(lambda: candidate.extract_metadata(html))
    emit(url=url, candidate_ms=ms, text_chars=len(getattr(doc, "text", "") or ""),
         metadata_ms=metadata_ms,
         has_title=bool(getattr(meta, "title", None)),
         has_author=bool(getattr(meta, "author", None)),
         has_date=bool(getattr(meta, "date", None)),
         has_image=bool(getattr(meta, "image", None)))


def check_discovery(package, url):
    import feedparser

    start = time.perf_counter()
    if package == "feed-seeker":
        from feed_seeker import generate_feed_urls

        found = list(itertools.islice(generate_feed_urls(url, max_time=12), 15))
    else:
        from feedsearch_crawler import search

        found = [str(feed.url) for feed in search(
            url, total_timeout=12, request_timeout=4, favicon_data_uri=False
        )][:15]
    elapsed = round(time.perf_counter() - start, 3)
    found = list(dict.fromkeys(map(str, found)))
    verified = []
    for link in found[:5]:
        try:
            parsed = feedparser.parse(download(link))
            if parsed.version and parsed.entries:
                verified.append(link)
        except Exception:
            continue
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
    emit(candidate=package, version=version(package))
    urls = FEEDS if package in {"fastfeedparser", "feedparser-rs"} else SITES
    if package in {"trafilatura", "rtrafilatura"}:
        urls = list(article_urls())
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
        except Exception as exc:
            emit(url=url, error=str(exc)[:300])


if __name__ == "__main__":
    main()
