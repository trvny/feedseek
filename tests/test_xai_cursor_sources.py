"""Cursor sources belong to the existing xAI aggregate."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))
import xai


class CursorSourcesTests(unittest.TestCase):
    def test_native_changelog_rss_and_sources(self):
        self.assertEqual(xai.CURSOR_CHANGELOG_URL, "https://cursor.com/changelog/rss.xml")
        self.assertEqual(xai.CURSOR_BLOG_URL, "https://cursor.com/blog")
        self.assertEqual(
            xai.CURSOR_RELEASE_NOTES_RSS_URL,
            "https://cursor.com/docs/release-notes/rss.xml",
        )
        self.assertIn(
            ("Cursor Release Notes", xai.CURSOR_RELEASE_NOTES_RSS_URL),
            xai.doc_sources(),
        )
        self.assertIn(("Cursor Changelog", xai.CURSOR_CHANGELOG_URL), xai.doc_sources())
        self.assertIn(("Cursor Blog", xai.CURSOR_BLOG_URL), xai.doc_sources())
        with patch.object(xai, "scrape_feed", return_value=[]) as native:
            self.assertEqual(xai.scrape_cursor_changelog({"https://cursor.com/old"}), [])
        native.assert_called_once_with(
            "Cursor Changelog", xai.CURSOR_CHANGELOG_URL,
            {"https://cursor.com/old"}, cap=50
        )
        with patch.object(xai, "scrape_feed", return_value=[]) as native:
            self.assertEqual(xai.scrape_cursor_release_notes(set()), [])
        native.assert_called_once_with(
            "Cursor Release Notes", xai.CURSOR_RELEASE_NOTES_RSS_URL,
            set(), cap=60
        )

    def test_grok_build_rss_preserves_html_history(self):
        """Native Build feed is additional, not a replacement for cached history."""
        self.assertEqual(xai.BUILD_RSS_URL, "https://x.ai/changelog/build/rss.xml")
        self.assertIn(("Grok Build changelog RSS", xai.BUILD_RSS_URL), xai.doc_sources())
        with patch.object(xai, "scrape_feed", return_value=[]) as native:
            self.assertEqual(xai.scrape_build_rss({"https://x.ai/old"}), [])
        native.assert_called_once_with(
            "Grok Build changelog", xai.BUILD_RSS_URL,
            {"https://x.ai/old"}, cap=60
        )

    def test_native_and_html_build_titles_deduplicate(self):
        """Parse both sources, then collapse duplicates through xAI.main."""

        rss = """
        <rss version="2.0"><channel><item>
          <title>Grok Build 1.0.32</title>
          <link>https://x.ai/changelog/build#v1-0-32</link>
          <pubDate>Mon, 14 Sep 2026 12:00:00 GMT</pubDate>
        </item></channel></rss>
        """
        html = """
        <h2 id="v1.0.32-2026-09-14">Grok Build 1.0.32</h2>
        <p>Improvements for MCP tools.</p>
        """
        with patch("multi_rss.get_html", return_value=rss):
            native = xai.scrape_build_rss(set())
        with patch.object(xai, "_get_html", return_value=html):
            legacy = xai.scrape_build_changelog(set())

        self.assertEqual(len(native), 1)
        self.assertEqual(len(legacy), 1)
        self.assertNotEqual(native[0]["link"], legacy[0]["link"])

        with (
            patch.object(xai, "load_cache", return_value={"entries": []}),
            patch.object(xai, "_seed_legacy_x_api_cache", return_value=[]),
            patch.object(xai, "scrape_all", return_value=native + legacy),
            patch.object(xai, "enrich_entries"),
            patch.object(xai, "save_cache") as save_cache,
            patch.object(xai, "save_atom_feed"),
        ):
            self.assertTrue(xai.main())

        merged = save_cache.call_args.args[1]
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["title"], "Grok Build 1.0.32")
        self.assertIn(
            merged[0]["link"], {native[0]["link"], legacy[0]["link"]}
        )

    def test_blog_listing_filters_navigation_duplicates_and_known(self):
        index = """
        <main>
          <a href="/blog/">Blog</a>
          <article>
            <a href="/blog/improved-token-efficiency?utm_source=site">
              <h2>Improved token efficiency</h2><span>Sep 23, 2026</span>
            </a>
          </article>
          <a href="/blog/improved-token-efficiency">Duplicate</a>
          <a href="/blog/older-post">Old</a>
          <a href="/blog/category/research">Category</a>
          <a href="https://other.example/blog/fake">External</a>
          <a href="/blog/another-post"><span>Sep 20, 2026</span></a>
        </main>
        """
        entries = xai._cursor_blog_index(index, {"https://cursor.com/blog/older-post"})
        self.assertEqual(
            [link for link, _, _ in entries],
            ["https://cursor.com/blog/improved-token-efficiency",
             "https://cursor.com/blog/another-post"]
        )
        self.assertEqual(entries[0][1].date().isoformat(), "2026-09-23")
        self.assertEqual(entries[0][2], "Improved token efficiency")

    def test_article_prefers_detail_heading_description_date_and_media(self):
        detail = """
        <head>
          <meta name="description" content="Better agent token usage.">
          <meta property="og:image" content="/media/preview.png">
          <meta property="article:published_time" content="2026-09-23T14:30:00Z">
        </head>
        <article><h1>Longer agent runs use fewer tokens</h1></article>
        """
        entry = xai._cursor_blog_article(
            detail, "https://cursor.com/blog/improved-token-efficiency", None
        )
        self.assertEqual(entry["title"], "Longer agent runs use fewer tokens")
        self.assertEqual(entry["date"].isoformat(), "2026-09-23T14:30:00+00:00")
        self.assertEqual(entry["image"], "https://cursor.com/media/preview.png")
        self.assertEqual(entry["description"], "Better agent token usage.")
        self.assertEqual(entry["source"], "Cursor Blog")

    def test_blog_uses_listing_date_and_skips_undated_unknown(self):
        index = """
        <article><a href="/blog/new-post">
          <h2>New post</h2><span>Oct 29, 2026</span>
        </a></article>
        <article><a href="/blog/undated"><h2>Undated</h2></a></article>
        """
        def fetch(url):
            if url == xai.CURSOR_BLOG_URL:
                return index
            if url.endswith("/new-post"):
                return '<article><h1>New post detail</h1></article>'
            return "<article><h1>Undated</h1></article>"
        with patch.object(xai, "_get_html", side_effect=fetch) as get:
            entries = xai.scrape_cursor_blog(set())
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["title"], "New post detail")
        self.assertEqual(entries[0]["date"].date().isoformat(), "2026-10-29")
        self.assertEqual(get.call_count, 3)


    def test_invalid_detail_date_falls_back_to_listing_date(self):
        entry = xai._cursor_blog_article(
            '<head><meta property="article:published_time" content="not a date"></head>'
            '<h1>Known entry</h1>',
            "https://cursor.com/blog/known-entry",
            xai.parse_date("Oct 29, 2026"),
        )
        self.assertEqual(entry["date"].date().isoformat(), "2026-10-29")

    def test_sibling_card_date_is_not_stolen(self):
        index = """
        <main><div class="listing">
          <article><a href="/blog/dated"><h2>Dated</h2></a><span>Oct 29, 2026</span></article>
          <article><a href="/blog/undated"><h2>Undated</h2></a></article>
        </div></main>
        """
        items = xai._cursor_blog_index(index, set())
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0][1].date().isoformat(), "2026-10-29")
        self.assertIsNone(items[1][1])


    def test_invalid_decimal_date_cannot_abort_collection(self):
        from decimal import InvalidOperation

        with patch.object(xai.date_parser, "parse", side_effect=InvalidOperation):
            self.assertIsNone(xai.parse_date("bad numeric timestamp"))
        index_date = xai.parse_date("Oct 29, 2026")
        detail = (
            '<head><meta property="article:published_time" content="bad numeric timestamp"></head>'
            '<h1>Still publishable</h1>'
        )
        with patch.object(xai.date_parser, "parse", side_effect=InvalidOperation):
            entry = xai._cursor_blog_article(
                detail, "https://cursor.com/blog/still-publishable", index_date
            )
        self.assertEqual(entry["date"], index_date)

    def test_discovery_budget_and_aggregate_invocation(self):
        index = "<main>" + "".join(
            f'<article><a href="/blog/post-{n}"><h2>Post {n}</h2>'
            f'<span>Oct 29, 2026</span></a></article>'
            for n in range(20)
        ) + "</main>"
        self.assertEqual(len(xai._cursor_blog_index(index, set())), xai.CURSOR_BLOG_MAX)
        with patch.object(xai, "_get_html", side_effect=lambda url: index if url == xai.CURSOR_BLOG_URL else "<h1>Detail</h1>") as get:
            self.assertEqual(len(xai.scrape_cursor_blog(set())), xai.CURSOR_BLOG_MAX)
        self.assertEqual(get.call_count, 1 + xai.CURSOR_BLOG_MAX)
        other_names = (
            "scrape_news", "scrape_console_changelog", "scrape_grok_bot_changelog",
            "scrape_tesla_blog", "scrape_build_changelog", "scrape_release_notes",
            "scrape_grok_release_notes", "scrape_x_blog", "scrape_x_api_changelog",
        )
        from contextlib import ExitStack

        with ExitStack() as stack:
            for name in other_names:
                stack.enter_context(patch.object(xai, name, return_value=[]))
            build_rss = stack.enter_context(
                patch.object(xai, "scrape_build_rss", return_value=[])
            )
            cursor_notes = stack.enter_context(
                patch.object(xai, "scrape_cursor_release_notes", return_value=[])
            )
            changelog = stack.enter_context(
                patch.object(xai, "scrape_cursor_changelog", return_value=[
                    {"title": "Cursor release"}
                ])
            )
            blog = stack.enter_context(
                patch.object(xai, "scrape_cursor_blog", return_value=[
                    {"title": "Cursor news"}
                ])
            )
            self.assertEqual(
                [entry["title"] for entry in xai.scrape_all(set())],
                ["Cursor release", "Cursor news"],
            )
            build_rss.assert_called_once_with(set())
            cursor_notes.assert_called_once_with(set())
            changelog.assert_called_once_with(set())
            blog.assert_called_once_with(set())

    def test_known_and_failed_index_skip_detail_fetches(self):
        index = '<a href="/blog/known"><h2>Known</h2><span>Oct 29, 2026</span></a>'
        with patch.object(xai, "_get_html", return_value=index) as get:
            self.assertEqual(xai.scrape_cursor_blog({"https://cursor.com/blog/known"}), [])
        get.assert_called_once_with(xai.CURSOR_BLOG_URL)
        with patch.object(xai, "_get_html", return_value=None):
            self.assertEqual(xai.scrape_cursor_blog(set()), [])


if __name__ == "__main__":
    unittest.main()
