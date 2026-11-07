"""Cursor sources have a single canonical aggregate after migration."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))
import saas
import xai


class CursorMigrationTests(unittest.TestCase):
    def test_cursor_sources_moved_from_saas_to_xai(self):
        self.assertNotIn("Cursor Changelog", {row[0] for row in saas.NATIVE_FEEDS})
        self.assertNotIn("Cursor Blog", {row[1] for row in saas.DATED_ANCHOR_SOURCES})
        self.assertIn("Cursor Changelog", saas.RETIRED_CACHE_SOURCES)
        self.assertIn("Cursor Blog", saas.RETIRED_CACHE_SOURCES)
        cached = [
            {"source": "Cursor Changelog", "link": "https://cursor.com/changelog/a"},
            {"source": "Cursor Blog", "link": "https://cursor.com/blog/b"},
            {"source": "Other", "link": "https://other.example"},
        ]
        self.assertEqual(saas._active_cached_entries(cached), cached[2:])
        self.assertIn(("Cursor Changelog", xai.CURSOR_CHANGELOG_URL), xai.doc_sources())
        self.assertIn(("Cursor Blog", xai.CURSOR_BLOG_URL), xai.doc_sources())


if __name__ == "__main__":
    unittest.main()
