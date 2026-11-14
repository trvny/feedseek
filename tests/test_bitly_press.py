import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))

import bitly


class PressTests(unittest.TestCase):
    def test_current_cards_and_legacy_coverage(self):
        page = """
          <div class="press-info"></div>
          <a class="card-news--internal" href="/pages/press/new-features/">
            <span>April 2, 2026</span><h3>New features</h3></a>
          <a class="card-news--external" href="https://example.com/coverage">
            <span>March 19, 2026</span><h3>External coverage</h3></a>
          <a class="card-news--internal" href="/pages/press/undated/">
            <h3>Undated</h3></a>
          <a class="card-news--internal" href="/pages/press/new-features/">
            <span>April 2, 2026</span><h3>Duplicate</h3></a>
        """
        with patch.object(bitly, "_get_html", return_value=page):
            entries = bitly.scrape_press(set())
        self.assertEqual(
            [entry["link"] for entry in entries],
            ["https://bitly.com/pages/press/new-features/", "https://example.com/coverage"],
        )
        self.assertEqual(entries[0]["date"].date().isoformat(), "2026-04-02")


if __name__ == "__main__":
    unittest.main()
