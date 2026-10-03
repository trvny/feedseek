"""Shared favicon routing stays stable for feeds and external readers."""

import sys
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))

from feedgen.feed import FeedGenerator  # noqa: E402

from utils import (  # noqa: E402
    FAVICON_PROXY_ORIGIN,
    favicon_proxy,
    favicon_url,
    large_icon,
    setup_feed_links,
)


def feed_with(feed_name, blog_url, icon=None):
    fg = FeedGenerator()
    fg.id(blog_url)
    fg.title(feed_name)
    setup_feed_links(fg, blog_url, feed_name, icon=icon)
    return fg


class ManagedIconTests(unittest.TestCase):
    def test_default_icon_uses_feedseek_resolver(self):
        icon = favicon_url("https://example.com/blog")
        parts = urlsplit(icon)

        self.assertEqual(
            f"{parts.scheme}://{parts.netloc}{parts.path}",
            FAVICON_PROXY_ORIGIN,
        )
        self.assertEqual(parse_qs(parts.query), {"domain": ["example.com"], "sz": ["64"]})

    def test_provider_preference_survives_the_stable_proxy(self):
        icon = favicon_proxy("nasa.gov", provider="duckduckgo", sz=32)
        query = parse_qs(urlsplit(icon).query)

        self.assertEqual(query["domain"], ["nasa.gov"])
        self.assertEqual(query["provider"], ["duckduckgo"])
        self.assertEqual(query["sz"], ["32"])

    def test_explicit_source_icon_is_preserved_as_first_resolver_candidate(self):
        fg = feed_with(
            "wykop",
            "https://wykop.pl/",
            icon="https://wykop.pl/static/img/favicons/favicon.png",
        )
        query = parse_qs(urlsplit(fg.icon()).query)

        self.assertEqual(query["domain"], ["wykop.pl"])
        self.assertEqual(
            query["url"],
            ["https://wykop.pl/static/img/favicons/favicon.png"],
        )

    def test_feed_gets_small_icon_and_large_logo_on_same_service(self):
        fg = feed_with("ubuntu", "https://ubuntu.com/blog")

        self.assertTrue(fg.icon().startswith(FAVICON_PROXY_ORIGIN))
        self.assertTrue(fg.logo().startswith(FAVICON_PROXY_ORIGIN))
        self.assertEqual(parse_qs(urlsplit(fg.icon()).query)["sz"], ["64"])
        self.assertEqual(parse_qs(urlsplit(fg.logo()).query)["sz"], ["256"])

    def test_large_icon_resizes_feedseek_and_google_resolvers_only(self):
        managed = favicon_proxy("example.com", sz=64)
        self.assertEqual(
            parse_qs(urlsplit(large_icon(managed)).query)["sz"],
            ["256"],
        )
        self.assertEqual(
            large_icon("https://www.google.com/s2/favicons?domain=x.test&sz=64"),
            "https://www.google.com/s2/favicons?domain=x.test&sz=256",
        )
        self.assertEqual(
            large_icon("https://example.com/icon.png?sz=1"),
            "https://example.com/icon.png?sz=1",
        )

    def test_unparseable_site_falls_back_without_inventing_a_domain(self):
        self.assertEqual(favicon_url("not a url"), "not a url")


if __name__ == "__main__":
    unittest.main()
