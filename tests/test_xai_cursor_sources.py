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
        self.assertIn(("Cursor Changelog", xai.CURSOR_CHANGELOG_URL), xai.doc_sources())
        self.assertIn(("Cursor Blog", xai.CURSOR_BLOG_URL), xai.doc_sources())
        with patch.object(xai, "scrape_feed", return_value=[]) as native:
            self.assertEqual(xai.scrape_cursor_changelog({"https://cursor.com/old"}), [])
        native.assert_called_once_with(
            "Cursor Changelog", xai.CURSOR_CHANGELOG_URL,
            {"https://cursor.com/old"}, cap=50
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

    def test_known_and_failed_index_skip_detail_fetches(self):
        index = '<a href="/blog/known"><h2>Known</h2><span>Oct 29, 2026</span></a>'
        with patch.object(xai, "_get_html", return_value=index) as get:
            self.assertEqual(xai.scrape_cursor_blog({"https://cursor.com/blog/known"}), [])
        get.assert_called_once_with(xai.CURSOR_BLOG_URL)
        with patch.object(xai, "_get_html", return_value=None):
            self.assertEqual(xai.scrape_cursor_blog(set()), [])


if __name__ == "__main__":
    unittest.main()
