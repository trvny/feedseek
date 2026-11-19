"""Bounded parsing of fetched XML. Native fast path, conservative fallback."""

import logging
import os
from importlib import import_module

import feedparser
from safe_feed_xml import FeedXmlError, parse_feed_xml

logger = logging.getLogger(__name__)


def _rust_parse(payload):
    import feedparser_rs

    return feedparser_rs.parse(payload)


def parse_headlines(payload: str | bytes):
    """RSS/Atom headline contract. No URL fetching."""
    data = payload.encode("utf-8") if isinstance(payload, str) else payload
    if not isinstance(data, bytes):
        raise TypeError("expected fetched feed bytes or text")
    if os.environ.get("FEEDSEEK_FEED_PARSER") != "python":
        try:
            root = parse_feed_xml(data).getroot()
            if root.tag == "rss":
                items = root.findall("./channel/item")
                date_tag = "pubDate"
            elif root.tag == "{http://www.w3.org/2005/Atom}feed":
                items = root.findall("{http://www.w3.org/2005/Atom}entry")
                date_tag = "{http://www.w3.org/2005/Atom}published"
            else:
                raise ValueError("unsupported fast-path format")
            parsed = _rust_parse(data)
            if parsed.bozo or len(parsed.entries) != len(items) or not items:
                raise ValueError("incomplete native result")
            for item, entry in zip(items, parsed.entries, strict=True):
                if not entry.get("title") or not entry.get("link"):
                    raise ValueError("missing headline or link")
                if item.findtext(date_tag) and not entry.get("published"):
                    raise ValueError("missing publication date")
            return parsed
        except (ImportError, FeedXmlError, ValueError, TypeError, AttributeError, KeyError, RuntimeError) as exc:
            logger.debug("Native headline parser fallback: %s", exc)
    return feedparser.parse(data)


def extract_article_metadata(html: str, *, accept):
    """First usable metadata result; HTML input only, no fetch."""
    if not html.lstrip().startswith("<"):
        return None
    for name in ("rtrafilatura", "trafilatura"):
        try:
            metadata = import_module(name).extract_metadata(html)
            if metadata is not None and (result := accept(metadata)):
                return result
        except Exception as exc:
            logger.debug("%s metadata fallback: %s", name, exc)
    return None
