"""Identity aliases remain usable after richer duplicate records arrive."""

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))

from utils import dedupe_entries  # noqa: E402

DATE = datetime(2026, 10, 28, tzinfo=timezone.utc)


class DedupeAliasTests(unittest.TestCase):
    def test_date_upgrade_registers_its_new_url_and_keeps_published_identity(self):
        original = {
            "link": "https://example.test/old",
            "title": "Story",
            "date": None,
            "entry_id": "published-id",
        }
        upgrade = {
            "link": "https://example.test/new",
            "title": "Story",
            "date": DATE,
            "entry_id": "other-id",
        }
        renamed = {"link": upgrade["link"], "title": "Renamed story", "date": DATE}
        result = dedupe_entries([original, upgrade, renamed])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["link"], upgrade["link"])
        self.assertEqual(result[0]["date"], DATE)
        self.assertEqual(result[0]["entry_id"], "published-id")
        self.assertEqual(upgrade["entry_id"], "other-id")

    def test_date_upgrade_registers_its_new_title(self):
        result = dedupe_entries(
            [
                {"link": "https://example.test/old", "title": "Draft", "date": None},
                {"link": "https://example.test/old", "title": "Published", "date": DATE},
                {"link": "https://example.test/new", "title": "Published", "date": DATE},
            ]
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "Published")

    def test_discarded_variants_still_register_identity_aliases(self):
        first = {"link": "https://example.test/one", "title": "First", "date": DATE}
        result = dedupe_entries(
            [
                first,
                {"link": first["link"], "title": "Alternative", "date": DATE},
                {"link": "https://example.test/two", "title": "Alternative", "date": DATE},
            ]
        )
        self.assertEqual(result, [first])

    def test_title_deduplication_can_still_be_disabled(self):
        items = [
            {"link": "https://example.test/one", "title": "Same", "date": None},
            {"link": "https://example.test/two", "title": "Same", "date": DATE},
        ]
        self.assertEqual(dedupe_entries(items, title_field=None), items)


if __name__ == "__main__":
    unittest.main()
