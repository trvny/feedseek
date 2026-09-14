import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))

from dji import (  # noqa: E402
    FORUM_HREF_RE,
    ISO_DATE_RE,
    MONTH_DATE_RE,
    _entries_from_listing,
    doc_sources,
)


class DjiFeedTests(unittest.TestCase):
    def test_doc_sources_lists_requested_surfaces(self):
        sources = doc_sources()
        self.assertEqual([label for label, _url in sources], [
            "DJI Announcements", "DJI ViewPoints", "DJI Forum"
        ])
        self.assertEqual(len(sources), 3)

    def test_announcements_strip_kind_and_date(self):
        html = """
        <div class="card">
          <a href="/media-center/announcements/dji-launches-widget">
            Product Releases DJI Launches Widget 2026-09-03
          </a>
        </div>
        """
        entries = _entries_from_listing(
            html,
            base_url="https://www.dji.com/pl/mobile/media-center/announcements",
            source="DJI Announcements",
            href_test=lambda href: "/media-center/announcements/" in href,
            date_pattern=ISO_DATE_RE,
        )
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["title"], "DJI Launches Widget")
        self.assertEqual(entries[0]["date"].isoformat(), "2026-09-03T00:00:00+00:00")

    def test_viewpoints_skips_read_more_and_uses_dated_title_link(self):
        html = """
        <article>
          <a href="/blog/security-update">Read More</a>
          <h2><a href="/blog/security-update">Security and Continuous Improvement</a></h2>
          <p>Mar 6, 2026</p>
        </article>
        """
        entries = _entries_from_listing(
            html,
            base_url="https://viewpoints.dji.com/blog",
            source="DJI ViewPoints",
            href_test=lambda href: "/blog/" in href,
            date_pattern=MONTH_DATE_RE,
        )
        self.assertEqual([entry["title"] for entry in entries], [
            "Security and Continuous Improvement"
        ])
        self.assertEqual(entries[0]["date"].isoformat(), "2026-03-06T00:00:00+00:00")

    def test_forum_recognizes_thread_links(self):
        html = """
        <div class="thread-row">
          <a href="thread-123456-1-1.html">10 tips to fly drones</a>
          <span>2026/08/23</span>
        </div>
        """
        entries = _entries_from_listing(
            html,
            base_url="https://forum.dji.com/",
            source="DJI Forum",
            href_test=lambda href: bool(FORUM_HREF_RE.search(href)),
            date_pattern=ISO_DATE_RE,
        )
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["source"], "DJI Forum")
        self.assertEqual(entries[0]["date"].isoformat(), "2026-08-23T00:00:00+00:00")


if __name__ == "__main__":
    unittest.main()
