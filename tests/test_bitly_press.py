import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))

import bitly


class PressTests(unittest.TestCase):
    def test_current_dated_press_cards(self):
        page = """
          <article><span>April 2, 2026</span><h3>
          <a href="/pages/resources/press/new-features/">New features</a>
          </h3></article>
          <article><span>March 19, 2026</span><h3>
          <a href="/pages/resources/press/new-cto/">New CTO</a>
          </h3></article>
          <article><h3><a href="/pages/resources/press/undated/">Undated</a></h3></article>
        """
        with patch.object(bitly, "_get_html", return_value=page):
            entries = bitly.scrape_press(set())
        self.assertEqual(
            [entry["link"] for entry in entries],
            [
                "https://bitly.com/pages/resources/press/new-features/",
                "https://bitly.com/pages/resources/press/new-cto/",
            ],
        )
        self.assertEqual(entries[0]["date"].date().isoformat(), "2026-04-02")


if __name__ == "__main__":
    unittest.main()
