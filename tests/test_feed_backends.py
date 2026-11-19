import importlib.util
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests

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
        with patch.object(feed_backends, "_rust_metadata", side_effect=ImportError()), patch.object(
            feed_backends, "_python_metadata", return_value=metadata
        ):
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
        with patch.object(discover, "discover_local", side_effect=requests.Timeout()), patch.object(
            discover, "discover_seeker", return_value=[]
        ), patch.object(discover, "discover_hosted", return_value=[]):
            self.assertEqual(discover.discover_target("https://example.com"), ([], "hosted"))

    def test_metadata_callback_error_is_not_swallowed(self):
        with patch.object(feed_backends, "_rust_metadata", return_value=Mock()), patch.object(
            feed_backends, "_python_metadata"
        ) as fallback:
            def invalid_callback(_):
                raise TypeError("callback bug")

            with self.assertRaises(TypeError):
                feed_backends.extract_article_metadata("<article>text</article>", accept=invalid_callback)
            fallback.assert_not_called()

    def test_html_programming_error_is_not_swallowed(self):
        with patch.dict(os.environ, {"FEEDSEEK_HTML_PARSER": "auto"}), patch(
            "article_image._fast_page_image", side_effect=TypeError("bug")
        ), self.assertRaises(TypeError):
            page_image("<html></html>", "https://example.com")

    def test_seeker_retains_partial_results_on_timeout(self):
        def urls():
            yield "https://example.com/rss"
            raise TimeoutError("deadline")

        module = Mock()
        module.FeedSeeker.return_value.generate_feed_urls.return_value = urls()
        with patch.dict(sys.modules, {"feed_seeker": module}):
            self.assertEqual(discover.discover_seeker("https://example.com"), [
                {"url": "https://example.com/rss"},
            ])
        module.FeedSeeker.assert_called_once()
        self.assertTrue(callable(module.FeedSeeker.call_args.kwargs["fetcher"]))

    def test_seeker_caps_unique_results_without_signal_timeout(self):
        module = Mock()
        module.FeedSeeker.return_value.generate_feed_urls.return_value = iter(
            ["https://example.com/0"] * 2 + [
                f"https://example.com/{index}" for index in range(1, 30)
            ]
        )
        with patch.dict(sys.modules, {"feed_seeker": module}):
            results = discover.discover_seeker("https://example.com")
        self.assertEqual(len(results), discover.SEEKER_MAX_RESULTS)
        self.assertEqual(results[-1]["url"], "https://example.com/14")
        module.FeedSeeker.return_value.generate_feed_urls.assert_called_once_with(
            max_links=discover.SEEKER_MAX_LINKS
        )

    def test_seeker_fetch_checks_deadline_before_request(self):
        session = Mock()
        with patch("discover.time.monotonic", return_value=10), self.assertRaises(TimeoutError):
            discover._seeker_fetch(session, "https://example.com", 10)
        session.get.assert_not_called()

    def test_unexpected_discovery_error_surfaces(self):
        with patch.object(discover, "discover_local", side_effect=TypeError("bug")), self.assertRaises(TypeError):
            discover.discover_target("https://example.com")
