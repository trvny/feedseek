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

    def test_drupal_polish_weekday_stamp_is_warsaw_wall_time(self):
        parsed = parse_date("czw., 10/29/2026 - 15:24")
        self.assertEqual(parsed.isoformat(), "2026-10-29T14:24:00+00:00")
        summer = parse_date("pon., 06/01/2026 - 09:05")
        self.assertEqual(summer.isoformat(), "2026-06-01T07:05:00+00:00")

    def test_english_rfc822_unchanged(self):
        parsed = parse_date("Thu, 29 Oct 2026 16:41:28 +0100")
        self.assertEqual(parsed.isoformat(), "2026-10-29T15:41:28+00:00")


if __name__ == "__main__":
    unittest.main()
