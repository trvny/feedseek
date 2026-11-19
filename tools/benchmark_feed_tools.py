"""Compare candidate libraries on bounded public Feedseek and upstream inputs."""
import argparse
import importlib
import itertools
import json
import statistics
import time
from importlib.metadata import version
from urllib.request import Request, urlopen

PAGES = "https://trvny.github.io/feedseek/"
FEEDS = [PAGES + key + ".xml" for key in (
    "jbzd", "beatport_top100", "openai", "github", "weather",
    "reuters", "arxiv", "wikipedia_pl",
)] + ["https://github.blog/feed/", "https://www.python.org/blogs/rss/",
      "https://www.independent.co.uk/rss", "https://www.indy100.com/feeds/feed.rss"]
SITES = ["https://www.independent.co.uk/", "https://www.indy100.com/",
         "https://github.blog/", "https://www.python.org/", "https://xkcd.com/"]
FIELDS = ("id", "title", "link", "published", "updated", "summary",
          "content", "author", "tags", "media_content", "enclosures")
MAX_BYTES = 8 * 1024 * 1024


def download(url):
    request = Request(url, headers={"User-Agent": "Feedseek benchmark/1.0"})
    with urlopen(request, timeout=15) as response:
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("response too large")
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
    emit(url=url, candidate_ms=ms, text_chars=len(getattr(doc, "text", "") or ""),
         has_title=bool(getattr(doc, "title", None)),
         has_author=bool(getattr(doc, "author", None)),
         has_date=bool(getattr(doc, "date", None)),
         has_image=bool(getattr(doc, "image", None)))


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

    for feed in ("https://github.blog/feed/", "https://www.python.org/blogs/rss/"):
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
