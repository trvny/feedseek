"""Foundry aggregate: all requested publishers and dated resource cards."""

import sys
import unittest
from threading import Barrier
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))

import foundry  # noqa: E402


class FoundryTests(unittest.TestCase):
    def test_all_requested_sites_have_native_feeds(self):
        self.assertEqual(
            {url for _, url, _ in foundry.SOURCES},
            {
                "https://foundryco.com/feed/",
                "https://www.csoonline.com/feed",
                "https://www.cio.com/feed",
                "https://www.pcworld.com/feed",
                "https://www.computerworld.com/feed",
                "https://www.infoworld.com/feed",
            },
        )

    def test_sitemap_parses_dated_cards_and_ignores_navigation(self):
        html = """
        <nav><h4><a href="/about/">About</a></h4></nav>
        <h4><a href="/article-one/">First report</a></h4>
        <p>Aug 31, 2026</p>
        <h4><a href="https://resources.foundryco.com/report.pdf">External study</a></h4>
        <p>Jun 04, 2026</p>
        <h4><a href="/article-one/">First report</a></h4>
        <p>Aug 31, 2026</p>
        <h4><a href="/missing-date/">No date</a></h4>
        <h4><a href="/next/">Next report</a></h4>
        <span>May 02, 2026</span>
        <h4><a href="/upcoming-event/">Future event</a></h4>
        <span>May 02, 2099</span>
        """
        entries = foundry.parse_sitemap(html, set())
        self.assertEqual(
            [e["link"] for e in entries],
            [
                "https://foundryco.com/article-one/",
                "https://resources.foundryco.com/report.pdf",
                "https://foundryco.com/next/",
            ],
        )
        self.assertEqual(entries[0]["date"].strftime("%Y-%m-%d"), "2026-08-31")
        self.assertEqual({e["source"] for e in entries}, {"Foundry Resources"})
        self.assertEqual(
            foundry.parse_sitemap(html, {"https://foundryco.com/article-one/"})[0]["title"],
            "External study",
        )

    def test_failed_sitemap_does_not_break_native_feed_run(self):
        with (
            patch.object(foundry.multi_rss, "get_html", return_value=None),
            patch.object(foundry.multi_rss, "run", return_value=True) as run,
        ):
            self.assertEqual(foundry.scrape_sitemap(set()), [])
            self.assertTrue(foundry.main())
        self.assertEqual(len(run.call_args.kwargs["sources"]), 6)
        self.assertEqual(run.call_args.kwargs["source_workers"], 6)
        self.assertIsNone(run.call_args.kwargs["dedupe_title_field"])
        self.assertEqual(run.call_args.kwargs["extra_scrapers"], (foundry.scrape_sitemap,))

    def test_concurrent_native_sources_preserve_source_order(self):
        barrier = Barrier(3)

        def scrape(label, url, known_links, **kwargs):
            barrier.wait(timeout=5)
            return [{"source": label, "link": url, "date": None}]

        sources = [
            ("A", "https://a.example/feed", 10),
            ("B", "https://b.example/feed", 10),
            ("C", "https://c.example/feed", 10),
        ]
        with patch.object(foundry.multi_rss, "scrape_feed", side_effect=scrape):
            refreshed, add_only = foundry.multi_rss._scrape_run_native_sources(
                sources, {"A", "B", "C"}, [], set(), source_workers=3
            )
        self.assertEqual([e["source"] for e in refreshed], ["A", "B", "C"])
        self.assertEqual(add_only, [])


if __name__ == "__main__":
    unittest.main()
