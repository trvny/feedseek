"""arXiv feed: arXiv blog + daily new submissions, adjacent research
commentary, and alphaXiv's public Explore page.

Native feeds remain the primary inputs. alphaXiv does not expose a public RSS
feed; its official headless MCP access requires an API key, so Explore is read
from the public server-rendered homepage as a best-effort extra source.

The new-submissions cap is deliberately low (50, not the feed's full window).
arXiv announces on the order of 200 abstracts per cycle, which would evict
every quieter source from the 500-entry feed within a couple of days. The
shared fair-share allocator keeps the combined history balanced, while the
alphaXiv scraper contributes at most 30 fresh cards per run.

LessWrong is pulled twice: the default feed.xml carries the newest posts,
while ?view=allPosts is the /allPosts listing and lags it by a few hours but
picks up items the default view omits. The two overlap heavily; shared dedupe
collapses duplicates by normalized link/title.
"""

from __future__ import annotations

import argparse
import re
import sys
from urllib.parse import urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup

from multi_rss import get_html, parse_date, run
from utils import sanitize_xml, setup_logging

logger = setup_logging()

FEED_NAME = "arxiv"
ALPHAXIV_URL = "https://www.alphaxiv.org/"
ALPHAXIV_SOURCE = "alphaXiv Explore"
ALPHAXIV_LIMIT = 30

SOURCES = [
    ("arXiv Blog", "https://blog.arxiv.org/feed/", 20),
    (
        "arXiv New Submissions",
        "https://rss.arxiv.org/atom/math+cs+econ+eess+astro-ph+cond-mat+gr-qc+"
        "hep-ex+hep-th+math-ph+nlin+nucl-th+physics+quant-ph+q-fin+stat",
        50,
    ),
    ("LessWrong", "https://www.lesswrong.com/feed.xml", 30),
    ("LessWrong (all posts)", "https://www.lesswrong.com/feed.xml?view=allPosts", 30),
    ("80,000 Hours", "https://80000hours.org/latest/feed/", 30),
]

_ALPHA_PAPER_PATH_RE = re.compile(r"^/abs/\d{4}\.\d{4,5}(?:v\d+)?/?$")
_ALPHA_DATE_RE = re.compile(r"\b\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}\b")


def _alphaxiv_link(href: object) -> str:
    """Return one canonical alphaXiv paper URL, or an empty string."""
    parts = urlsplit(urljoin(ALPHAXIV_URL, str(href or "").strip()))
    if parts.hostname not in {"alphaxiv.org", "www.alphaxiv.org"}:
        return ""
    path = parts.path.rstrip("/")
    if not _ALPHA_PAPER_PATH_RE.fullmatch(path):
        return ""
    return urlunsplit(("https", "www.alphaxiv.org", path, "", ""))


def _alphaxiv_scope(anchor):
    """Find the smallest nearby card that contains the paper's visible date."""
    fallback = anchor.parent
    for parent in anchor.parents:
        if getattr(parent, "name", None) in {"main", "body", "html"}:
            break
        if getattr(parent, "name", None) not in {"article", "li", "section", "div"}:
            continue
        paper_links = [
            item
            for item in parent.find_all("a", href=True)
            if _alphaxiv_link(item.get("href"))
        ]
        text = parent.get_text(" ", strip=True)
        if len(paper_links) <= 2 and _ALPHA_DATE_RE.search(text):
            return parent
        if parent.name in {"article", "li"}:
            fallback = parent
    return fallback or anchor


def parse_alphaxiv(html: str, known_links=()) -> list[dict]:
    """Parse recent paper cards from alphaXiv's public Explore homepage."""
    soup = BeautifulSoup(html or "", "html.parser")
    known = {_alphaxiv_link(link) for link in known_links}
    entries = []
    seen = set()

    for anchor in soup.find_all("a", href=True):
        link = _alphaxiv_link(anchor.get("href"))
        if not link or link in known or link in seen:
            continue

        title = sanitize_xml(anchor.get_text(" ", strip=True)).strip()
        if not title:
            continue

        scope = _alphaxiv_scope(anchor)
        visible = scope.get_text(" ", strip=True)
        date_match = _ALPHA_DATE_RE.search(visible)
        published = parse_date(date_match.group(0)) if date_match else None

        summaries = [
            sanitize_xml(paragraph.get_text(" ", strip=True)).strip()
            for paragraph in scope.find_all("p")
        ]
        summaries = [summary for summary in summaries if summary and summary != title]
        description = max(summaries, key=len, default=title)[:700]

        entries.append(
            {
                "title": title,
                "link": link,
                "date": published,
                "description": description,
                "source": ALPHAXIV_SOURCE,
            }
        )
        seen.add(link)
        if len(entries) >= ALPHAXIV_LIMIT:
            break

    return entries


def collect_alphaxiv(known_links) -> list[dict]:
    """Fetch alphaXiv Explore without making it a hard dependency."""
    html = get_html(ALPHAXIV_URL)
    if not html:
        return []
    entries = parse_alphaxiv(html, known_links)
    if not entries:
        logger.warning("[alphaXiv] no new paper cards matched")
    return entries


def doc_sources():
    """Expose native feeds plus the scraped alphaXiv Explore surface."""
    return [(label, url) for label, url, _cap in SOURCES] + [
        (ALPHAXIV_SOURCE, ALPHAXIV_URL)
    ]


def main(full=False):
    return run(
        feed_name=FEED_NAME,
        title="arXiv",
        subtitle=(
            "arXiv blog and daily new submissions, alphaXiv Explore, LessWrong, "
            "and 80,000 Hours."
        ),
        blog_url="https://arxiv.org/",
        author="various",
        sources=SOURCES,
        extra_scrapers=(collect_alphaxiv,),
        max_entries=500,
        full=full,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate the arXiv Atom feed")
    parser.add_argument(
        "--full", action="store_true", help="Ignore cache and rebuild from scratch"
    )
    sys.exit(0 if main(full=parser.parse_args().full) else 1)
