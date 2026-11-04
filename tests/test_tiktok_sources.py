"""Static parser checks for new official source integrations."""

import sys
import unittest
from unittest.mock import patch
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))

from tiktok import _parse_newsroom_listing, _parse_profile_html, doc_sources, main  # noqa: E402
from xai import GROK_BOT_RSS_URL, _parse_tesla_blog, _select_feed_items  # noqa: E402


class NewSourceTests(unittest.TestCase):
    def test_xai_grok_bot_has_official_rss(self):
        self.assertEqual(GROK_BOT_RSS_URL, "https://x.ai/changelog/bot/rss.xml")

    def test_tesla_dated_card(self):
        html = """
        <article>
          <h2>Standardizing Automotive Connectivity</h2>
          <p>The Tesla Team, October 27, 2024</p>
          <a href="/blog/standardizing-automotive-connectivity">Continue Reading</a>
        </article>"""
        items = _parse_tesla_blog(html)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "Standardizing Automotive Connectivity")
        self.assertEqual(items[0]["date"].year, 2024)

    def test_infrequent_tesla_posts_are_visible(self):
        base = datetime(2026, 1, 1, tzinfo=UTC)
        entries = [
            {"link": f"https://x.ai/news/{i}", "date": base + timedelta(days=i), "source": "xAI News"}
            for i in range(205)
        ]
        entries.extend([
            {"link": f"https://www.tesla.com/blog/{i}", "date": datetime(2024, 1, i + 1, tzinfo=UTC), "source": "Tesla Blog"}
            for i in range(5)
        ])
        result = _select_feed_items(sorted(entries, key=lambda entry: entry["date"]))
        self.assertEqual(len(result), 200)
        self.assertEqual(sum(entry["source"] == "Tesla Blog" for entry in result), 5)

    def test_tesla_does_not_invent_dates(self):
        self.assertEqual(
            _parse_tesla_blog('<a href="/blog/undated-story">Undated story</a>'),
            [],
        )

    def test_newsroom_dated_card(self):
        html = """
        <article>
          <time>July 13, 2026</time>
          <h2><a href="/tiktok-live-music-record?lang=en">TikTok LIVE Music Record</a></h2>
          <p>Millions watched.</p>
        </article>"""
        items = _parse_newsroom_listing(html)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["date"].year, 2026)
        self.assertEqual(items[0]["title"], "TikTok LIVE Music Record")

    def test_newsroom_skips_undated_links(self):
        self.assertEqual(
            _parse_newsroom_listing('<a href="/random-undated-story">Read more</a>'),
            [],
        )

    def test_tesla_undated_neighbor_does_not_borrow_date(self):
        html = """
        <div>
          <article>
            <h2>Dated announcement</h2>
            <p>The Tesla Team, October 27, 2024</p>
            <a href="/blog/dated-announcement">Continue Reading</a>
          </article>
          <a href="/blog/undated-story">Undated story</a>
        </div>"""
        self.assertEqual(
            [item["link"] for item in _parse_tesla_blog(html)],
            ["https://www.tesla.com/blog/dated-announcement"],
        )

    def test_newsroom_undated_neighbor_does_not_borrow_date(self):
        html = """
        <div>
          <article>
            <time>July 13, 2026</time>
            <h2>TikTok LIVE Music Record</h2>
            <a href="/tiktok-live-music-record?lang=en">Read</a>
          </article>
          <a href="/random-undated-story">Read more</a>
        </div>"""
        self.assertEqual(
            [item["link"] for item in _parse_newsroom_listing(html)],
            ["https://newsroom.tiktok.com/tiktok-live-music-record?lang=en"],
        )

    def test_short_newsroom_headline(self):
        html = """
        <article>
          <time>July 13, 2026</time>
          <h2>Hi!</h2>
          <a href="/brief-announcement">Read more</a>
        </article>"""
        self.assertEqual(
            [item["title"] for item in _parse_newsroom_listing(html)], ["Hi!"]
        )

    def test_video_identity_uses_url_not_caption(self):
        with patch("tiktok.run", return_value=True) as mocked:
            self.assertTrue(main())
        self.assertIsNone(mocked.call_args.kwargs["dedupe_title_field"])

    def test_tiktok_profile_hydration(self):
        html = """
        <script id="SIGI_STATE" type="application/json">
        {"ItemModule":{"7399999999999999999":{
          "id":"7399999999999999999",
          "author":"tiktok",
          "createTime":1720000000,
          "desc":"Official TikTok video"
        }}}
        </script>"""
        items = _parse_profile_html(html)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["source"], "TikTok @tiktok")
        self.assertEqual(items[0]["date"].year, 2024)

    def test_docs_use_official_tiktok_sources(self):
        self.assertEqual(
            [label for label, _ in doc_sources()],
            ["TikTok Newsroom", "TikTok @tiktok"],
        )


if __name__ == "__main__":
    unittest.main()
