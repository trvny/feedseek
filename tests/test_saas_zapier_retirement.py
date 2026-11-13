"""Retired Zapier articles must not return from the rolling SaaS cache."""

import importlib
import sys
import unittest
from contextlib import ExitStack
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))
saas = importlib.import_module("saas")


class ZapierRetirementTests(unittest.TestCase):
    """Exclude the broken source without dropping unrelated SaaS history."""

    def test_zapier_source_is_retired(self):
        """Disable native fetch; cache purge is tested via generation below."""
        urls = [url for _, url, _ in saas.NATIVE_FEEDS]
        self.assertNotIn("https://zapier.com/blog/feeds/latest/", urls)
        self.assertIn("https://blog.apify.com/rss/", urls)
        self.assertIn("Zapier", saas.RETIRED_CACHE_SOURCES)

    def test_incremental_generation_persists_without_zapier(self):
        """A normal refresh cleans the durable cache, not just the XML."""
        date = datetime(2026, 11, 13, tzinfo=UTC)
        cached = [
            {
                "id": "https://zapier.com/blog/coda-vs-notion",
                "link": "https://zapier.com/blog/coda-vs-notion",
                "title": "Old comparison",
                "date": datetime(2027, 11, 10, tzinfo=UTC),
                "source": "Zapier",
            },
            {
                "id": "https://vercel.com/blog/healthy",
                "link": "https://vercel.com/blog/healthy",
                "title": "Healthy update",
                "date": date,
                "source": "Vercel",
            },
        ]
        collectors = (
            "collect_hcp", "collect_bitly", "collect_commoninja",
            "collect_native_feeds", "collect_stripe", "collect_coderabbit_newsroom",
            "collect_postman_app_release_notes", "collect_postman_press",
            "collect_exa_blog", "collect_dated_anchor_sources",
        )
        serialized = [{**entry, "date": entry["date"].isoformat()} for entry in cached]
        with ExitStack() as stack:
            stack.enter_context(
                patch.object(saas, "load_cache", return_value={"entries": serialized})
            )
            for name in collectors:
                stack.enter_context(patch.object(saas, name, return_value=[]))
            stack.enter_context(patch.object(saas, "enrich_entries"))
            atom = stack.enter_context(
                patch.object(saas, "generate_atom_feed", return_value="atom")
            )
            saved = stack.enter_context(patch.object(saas, "save_cache"))
            published = stack.enter_context(patch.object(saas, "save_atom_feed"))
            self.assertTrue(saas.main())

        self.assertEqual(saved.call_args.args[0], "saas")
        self.assertEqual(
            [item["source"] for item in saved.call_args.args[1]], ["Vercel"]
        )
        self.assertEqual(
            [entry["source"] for entry in atom.call_args.args[0]], ["Vercel"]
        )
        published.assert_called_once_with("atom", "saas")


if __name__ == "__main__":
    unittest.main()
