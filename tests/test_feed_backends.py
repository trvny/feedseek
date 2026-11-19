import importlib.util
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))

import discover
import feed_backends
from article_image import _fast_page_image, page_image

XML = b"""<rss version="2.0"><channel><title>Example</title><item>
<title>A</title><link>https://example.com/a</link>
<pubDate>Wed, 18 Nov 2026 12:00:00 GMT</pubDate></item></channel></rss>"""


class FeedBackendTests(unittest.TestCase):
    def test_headlines_match_legacy(self):
        with patch.dict(os.environ, {"FEEDSEEK_FEED_PARSER": "python"}):
            legacy = feed_backends.parse_headlines(XML).entries[0]
        with patch.dict(os.environ, {"FEEDSEEK_FEED_PARSER": "auto"}):
            native = feed_backends.parse_headlines(XML).entries[0]
        for key in ("title", "link", "published"):
            self.assertEqual(native.get(key), legacy.get(key))

    @unittest.skipUnless(importlib.util.find_spec("feedparser_rs"), "native parser unavailable")
    def test_installed_native_parser_does_not_use_fallback(self):
        with patch.dict(os.environ, {"FEEDSEEK_FEED_PARSER": "auto"}), patch.object(
            feed_backends.feedparser, "parse", side_effect=AssertionError("legacy parser used")
        ):
            native = feed_backends.parse_headlines(XML)
            self.assertEqual(native.entries[0].get("link"), "https://example.com/a")

    def test_native_failure_and_empty_result_fall_back(self):
        for result in (Mock(bozo=True), Mock(bozo=False, entries=[])):
            with patch.dict(os.environ, {"FEEDSEEK_FEED_PARSER": "auto"}), patch.object(
                feed_backends, "_rust_parse", return_value=result
            ):
                self.assertEqual(feed_backends.parse_headlines(XML).entries[0].link, "https://example.com/a")

    def test_native_returned_on_valid_result(self):
        native = Mock(bozo=False, entries=[{
            "title": "A", "link": "https://example.com/a",
            "published": "Wed, 18 Nov 2026 12:00:00 GMT",
        }])
        with patch.dict(os.environ, {"FEEDSEEK_FEED_PARSER": "auto"}), patch.object(
            feed_backends, "_rust_parse", return_value=native
        ):
            self.assertIs(feed_backends.parse_headlines(XML), native)

    def test_html_fast_path_matches_legacy(self):
        html = '<meta property="og:image" content="/hero.jpg"><meta property="og:image:width" content="1200">'
        with patch.dict(os.environ, {"FEEDSEEK_HTML_PARSER": "beautifulsoup"}):
            legacy = page_image(html, "https://example.com/a")
        with patch.dict(os.environ, {"FEEDSEEK_HTML_PARSER": "auto"}):
            self.assertEqual(page_image(html, "https://example.com/a"), legacy)
        self.assertEqual(_fast_page_image(html, "https://example.com/a"), legacy)

    def test_metadata_fallback(self):
        metadata = Mock(image="https://example.com/a.jpg", title="Article")
        module = Mock()
        module.extract_metadata.return_value = metadata
        with patch.object(feed_backends, "import_module", side_effect=[ImportError(), module]):
            self.assertEqual(
                feed_backends.extract_article_metadata("<article>text</article>", accept=lambda doc: doc.image),
                metadata.image,
            )

    def test_discovery_fallbacks(self):
        with patch.object(discover, "discover_local", return_value=[]), patch.object(
            discover, "discover_seeker", return_value=[{"url": "https://example.com/rss"}]
        ), patch.object(discover, "discover_hosted") as hosted:
            self.assertEqual(discover.discover_target("https://example.com")[1], "seeker")
            hosted.assert_not_called()
        with patch.object(discover, "discover_local", side_effect=RuntimeError()), patch.object(
            discover, "discover_seeker", return_value=[]
        ), patch.object(discover, "discover_hosted", return_value=[]):
            self.assertEqual(discover.discover_target("https://example.com"), ([], "hosted"))
