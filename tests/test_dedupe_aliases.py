"""Identity aliases remain usable after richer duplicate records arrive."""

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))

from utils import dedupe_entries, normalize_link  # noqa: E402

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
                # Title duplicate with its own URL: discarded, but its URL must alias `first`.
                {"link": "https://example.test/alt", "title": "First", "date": DATE},
                # Matches only through that URL alias.
                {"link": "https://example.test/alt", "title": "Unrelated", "date": DATE},
            ]
        )
        self.assertEqual(result, [first])

    def test_discarded_variants_still_register_title_aliases(self):
        first = {"link": "https://example.test/one", "title": "First", "date": DATE}
        result = dedupe_entries(
            [
                first,
                {"link": first["link"], "title": "Alternative", "date": DATE},
                {"link": "https://example.test/two", "title": "Alternative", "date": DATE},
            ]
        )
        self.assertEqual(result, [first])

    def test_opaque_ids_do_not_turn_into_http_urls(self):
        cases = ["urn:uuid:abc", "id-123", "/relative", "mailto:a@example.com"]
        for key in cases:
            with self.subTest(key=key):
                self.assertEqual(normalize_link(key), key)

    def test_http_credentials_are_removed_from_published_link(self):
        self.assertEqual(
            normalize_link("https://user:secret@example.com/post"),
            "https://example.com/post",
        )

    def test_ipv6_url_keeps_valid_authority(self):
        self.assertEqual(
            normalize_link("http://[2001:db8::1]:8080/story?utm_source=x&id=2#part"),
            "https://[2001:db8::1]:8080/story?id=2#part",
        )

    def test_distinct_opaque_ids_remain_distinct(self):
        items = [{"id": key} for key in ("urn:abc", "urn:def", "abc", "def")]
        self.assertEqual(dedupe_entries(items, id_field="id", title_field=None), items)

    def test_title_deduplication_can_still_be_disabled(self):
        items = [
            {"link": "https://example.test/one", "title": "Same", "date": None},
            {"link": "https://example.test/two", "title": "Same", "date": DATE},
        ]
        self.assertEqual(dedupe_entries(items, title_field=None), items)


if __name__ == "__main__":
    unittest.main()
