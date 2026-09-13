import sys
import unittest
from pathlib import Path
from unittest.mock import mock_open, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))

from models import load_feed_registry, load_published_feeds  # noqa: E402


class FeedRegistryTests(unittest.TestCase):
    def test_published_feeds_keep_order_and_title_overrides(self):
        registry = """\
published_feeds:
  - reuters
  - name: daily_digest
    title: Daily — Curated
feeds:
  reuters: {}
  daily_digest: {}
"""
        with patch("builtins.open", mock_open(read_data=registry)):
            self.assertEqual(
                load_published_feeds(),
                [("reuters", ""), ("daily_digest", "Daily — Curated")],
            )

    def test_published_feeds_reject_duplicates_and_unknown_names(self):
        duplicate = """\
published_feeds: [reuters, reuters]
feeds:
  reuters: {}
"""
        with patch("builtins.open", mock_open(read_data=duplicate)):
            with self.assertRaisesRegex(ValueError, "duplicate feed: reuters"):
                load_published_feeds()

        unknown = """\
published_feeds: [missing]
feeds:
  reuters: {}
"""
        with patch("builtins.open", mock_open(read_data=unknown)):
            with self.assertRaisesRegex(ValueError, "unknown feed: missing"):
                load_published_feeds()


    def test_non_mapping_feed_configs_are_skipped(self):
        registry = """\
feeds:
  good:
    script: beatport_top100.py
    blog_url: https://example.com/
  null_config:
  list_config:
    - not
    - a
    - mapping
"""

        with patch("builtins.open", mock_open(read_data=registry)):
            feeds, skipped = load_feed_registry(return_skipped=True)

        self.assertEqual(set(feeds), {"good"})
        self.assertEqual(skipped, ["null_config", "list_config"])


if __name__ == "__main__":
    unittest.main()
