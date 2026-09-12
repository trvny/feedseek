import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))

from multi_rss import parse_date


class MultiRssDateTests(unittest.TestCase):
    def test_polish_genitive_month_names(self):
        cases = {
            "24 sierpnia 2026": (2026, 8, 24),
            "30 kwietnia 2026": (2026, 4, 30),
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                parsed = parse_date(raw)
                self.assertIsNotNone(parsed)
                self.assertEqual((parsed.year, parsed.month, parsed.day), expected)


if __name__ == "__main__":
    unittest.main()
