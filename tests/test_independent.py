import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))

import independent  # noqa: E402


class IndependentTests(unittest.TestCase):
    def test_rss_uses_only_direct_headlines_and_dates(self):
        xml = """<rss version="2.0"><channel><title>Feed</title>
        <item><title>Story</title><link>https://www.independent.co.uk/news/story.html?track=1</link>
        <pubDate>Wed, 18 Nov 2026 12:00:00 GMT</pubDate><description>Do not republish this</description></item>
        <item><title>Foreign</title><link>https://example.com/news/story</link></item>
        </channel></rss>"""
        rows = independent.parse_rss(xml, independent.BASE_URL, "The Independent")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["link"], "https://www.independent.co.uk/news/story.html")
        self.assertEqual(rows[0]["description"], "Story")
        self.assertEqual(rows[0]["date_kind"], "published")
        self.assertNotIn("image", rows[0])

    def test_listing_skips_navigation_and_marks_discovery_time(self):
        html = """<h2><a href="/news/">News</a></h2>
        <h2><a href="/politics/trump">Trump</a></h2>
        <h2><a href="/gaming/major-game-story">Game story</a></h2>
        <a href="/gaming/major-game-story"><h3>Duplicate</h3></a>
        <h2><a href="https://other.test/news/foreign">Foreign</a></h2>"""
        rows = independent.parse_indy_listing(html)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["date_kind"], "first_seen")
        self.assertEqual(rows[0]["title"], "Game story")

    def test_indy_falls_back_to_listing(self):
        with patch.object(independent, "get_html", side_effect=[None, '<h2><a href="/viral/new-viral-story">Story</a></h2>']):
            self.assertEqual(independent.scrape_indy100(set())[0]["source"], "Indy100")

    def test_stale_native_feed_does_not_block_listing(self):
        xml = """<rss version="2.0"><channel><title>Old feed</title>
        <item><title>Old</title><link>https://www.indy100.com/viral/old-viral-story</link>
        <pubDate>Fri, 19 Dec 2025 12:00:00 GMT</pubDate></item></channel></rss>"""
        html = '<h2><a href="/viral/new-viral-story">New</a></h2>'
        with patch.object(independent, "get_html", side_effect=[xml, html]):
            rows = independent.scrape_indy100(set())
        self.assertEqual([row["title"] for row in rows], ["New"])


if __name__ == "__main__":
    unittest.main()
