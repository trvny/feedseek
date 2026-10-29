import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))

import trojka


def _card(**fields):
    base = {"alt": "x", "id": "a1", "href": "/kultura/tytul", "title": "Tytuł", "lead": "Lead",
            "publishDate": "2026-10-29T19:49:51.193515+01:00", "category": "Kultura",
            "imageUrl": "https://cdn6.polskieradio.pl/img.jpeg", "isSponsored": False}
    base.update(fields)
    return base


def _page(*cards):
    payload = '0:["$","div",null,{"items":' + json.dumps(list(cards), ensure_ascii=False) + "}]"
    half = len(payload) // 2
    pushes = "".join(
        f"<script>self.__next_f.push([1,{json.dumps(part, ensure_ascii=False)}])</script>"
        for part in (payload[:half], payload[half:])
    )
    return f"<html><body>{pushes}</body></html>"


class TrojkaRscTests(unittest.TestCase):
    def test_parses_cards_across_split_flight_chunks(self):
        posts = trojka.parse_posts(_page(_card()))
        self.assertEqual(len(posts), 1)
        post = posts[0]
        self.assertEqual(post["link"], "https://trojka.polskieradio.pl/kultura/tytul")
        self.assertEqual(post["title"], "Tytuł")
        self.assertEqual(post["date"].isoformat(), "2026-10-29T19:49:51.193515+01:00")
        self.assertEqual(post["category"], "Kultura")

    def test_skips_foreign_hosts_sponsored_and_repeats(self):
        seen = set()
        html = _page(
            _card(),
            _card(id="a2", href="https://polskieradio24.pl/swiat/x"),
            _card(id="a3", href="/muzyka/y", isSponsored=True),
        )
        self.assertEqual(len(trojka.parse_posts(html, seen)), 1)
        self.assertEqual(trojka.parse_posts(_page(_card()), seen), [])

    def test_missing_flight_data_is_an_error(self):
        with self.assertRaises(ValueError):
            trojka.parse_posts("<html></html>")


if __name__ == "__main__":
    unittest.main()
