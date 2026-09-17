import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))

import czworka
from czworka import (
    FETCH_BASE_URL,
    PUBLIC_BASE_URL,
    _canonical,
    discover_links,
)


class CzworkaTests(unittest.TestCase):
    def test_canonical_keeps_existing_public_article_identity(self):
        self.assertEqual(
            _canonical(
                "https://czworka.online/10/216/Artykul/3718215,"
                "Zdjecia-do-drugiej-czesci"
            ),
            "https://www.polskieradio.pl/10/216/Artykul/3718215",
        )

    def test_discovery_prefers_public_article_host(self):
        html = (
            '<a href="/10/216/Artykul/3718215,example">Czwórka</a>'
            '<a href="/7/123/Artykul/9999999,other">Jedynka</a>'
        )

        self.assertEqual(
            discover_links(html),
            [f"{PUBLIC_BASE_URL}/10/216/Artykul/3718215,example"],
        )

    def test_fetch_article_falls_back_to_dedicated_host(self):
        url = f"{PUBLIC_BASE_URL}/10/218/Artykul/3732406"
        html = (
            '<meta property="og:title" content="Test title">'
            '<meta property="og:description" content="Test lead">'
        )

        with patch.object(czworka, "fetch_page", side_effect=[RuntimeError("404"), html]) as fetch:
            post = czworka.fetch_article(url)

        self.assertEqual(post["link"], url)
        self.assertEqual(post["title"], "Test title")
        self.assertEqual(
            [call.args[0] for call in fetch.call_args_list],
            [url, f"{FETCH_BASE_URL}/10/218/Artykul/3732406"],
        )

    def test_main_keeps_last_good_feed_when_new_article_fetch_fails(self):
        old = {"link": f"{PUBLIC_BASE_URL}/10/218/Artykul/1"}
        new = f"{PUBLIC_BASE_URL}/10/218/Artykul/2"
        with (
            patch.object(czworka, "load_cache", return_value={"entries": [{}]}),
            patch.object(czworka, "deserialize_entries", return_value=[old]),
            patch.object(czworka, "fetch_homepage_links", return_value=[new]),
            patch.object(czworka, "fetch_new_articles", return_value=([], [new])),
            patch.object(czworka, "save_cache") as save_cache,
            patch.object(czworka, "save_atom_feed") as save_atom_feed,
        ):
            self.assertFalse(czworka.main())

        save_cache.assert_not_called()
        save_atom_feed.assert_not_called()


if __name__ == "__main__":
    unittest.main()
