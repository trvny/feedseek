"""Tests for the post-generation feed metadata normalizer."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))

from normalize_feed_self_links import (  # noqa: E402  # pylint: disable=wrong-import-position
    CURRENT_PREFIX,
    LEGACY_PREFIX,
    normalize_feed_self_links,
)
from utils import FAVICON_PROXY_ORIGIN  # noqa: E402  # pylint: disable=wrong-import-position


def _tag_value(content, tag):
    start = content.index(f"<{tag}>") + len(tag) + 2
    return content[start : content.index(f"</{tag}>", start)].replace("&amp;", "&")


class NormalizeFeedSelfLinksTests(unittest.TestCase):
    """Cover self-link cleanup and durable favicon migration."""

    def test_rewrites_legacy_prefix_without_touching_non_atom_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            feeds_dir = Path(tmp)
            legacy = feeds_dir / "feed_jbzd.xml"
            current = feeds_dir / "feed_trojka.xml"
            legacy.write_text(
                f'<rss><link>{LEGACY_PREFIX}feed_jbzd.xml</link></rss>',
                encoding="utf-8",
            )
            current.write_text(
                f'<rss><link>{CURRENT_PREFIX}feed_trojka.xml</link></rss>',
                encoding="utf-8",
            )

            changed = normalize_feed_self_links(feeds_dir)

            self.assertEqual(changed, [legacy])
            self.assertIn(
                f"{CURRENT_PREFIX}feed_jbzd.xml",
                legacy.read_text(encoding="utf-8"),
            )
            self.assertEqual(
                current.read_text(encoding="utf-8"),
                f"<rss><link>{CURRENT_PREFIX}feed_trojka.xml</link></rss>",
            )

    def test_ignores_non_xml_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            feeds_dir = Path(tmp)
            sidecar = feeds_dir / "feed_jbzd.json"
            sidecar.write_text(LEGACY_PREFIX, encoding="utf-8")

            changed = normalize_feed_self_links(feeds_dir)

            self.assertEqual(changed, [])
            self.assertEqual(sidecar.read_text(encoding="utf-8"), LEGACY_PREFIX)

    def test_migrates_root_favicon_to_managed_icon_and_large_logo(self):
        with tempfile.TemporaryDirectory() as tmp:
            feeds_dir = Path(tmp)
            feed = feeds_dir / "feed_newsify.xml"
            feed.write_text(
                """<feed xmlns="http://www.w3.org/2005/Atom">
  <id>https://newsify.today/</id>
  <title>Newsify</title>
  <link href="https://newsify.today/polish/PL" rel="alternate"/>
  <icon>https://newsify.today/favicon.ico</icon>
  <logo>https://newsify.today/favicon.ico</logo>
</feed>
""",
                encoding="utf-8",
            )

            changed = normalize_feed_self_links(feeds_dir)
            rendered = feed.read_text(encoding="utf-8")
            icon = _tag_value(rendered, "icon")
            logo = _tag_value(rendered, "logo")

            self.assertEqual(changed, [feed])
            self.assertTrue(icon.startswith(FAVICON_PROXY_ORIGIN))
            self.assertEqual(
                parse_qs(urlsplit(icon).query),
                {"domain": ["newsify.today"], "sz": ["64"]},
            )
            self.assertEqual(parse_qs(urlsplit(logo).query)["sz"], ["256"])

    def test_migrates_old_third_party_resolver_without_preserving_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            feeds_dir = Path(tmp)
            feed = feeds_dir / "feed_jbzd.xml"
            feed.write_text(
                """<feed xmlns="http://www.w3.org/2005/Atom">
  <id>https://jbzd.com.pl/</id>
  <title>JBZD</title>
  <link href="https://jbzd.com.pl/" rel="alternate"/>
  <icon>https://www.google.com/s2/favicons?domain=jbzd.com.pl&amp;sz=64</icon>
</feed>
""",
                encoding="utf-8",
            )

            normalize_feed_self_links(feeds_dir)
            icon = _tag_value(feed.read_text(encoding="utf-8"), "icon")
            query = parse_qs(urlsplit(icon).query)

            self.assertEqual(query["domain"], ["jbzd.com.pl"])
            self.assertEqual(query["sz"], ["64"])
            self.assertNotIn("url", query)

    def test_preserves_explicit_source_asset_as_first_server_side_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            feeds_dir = Path(tmp)
            feed = feeds_dir / "feed_wykop.xml"
            explicit = "https://wykop.pl/static/img/favicons/favicon.png"
            feed.write_text(
                f"""<feed xmlns="http://www.w3.org/2005/Atom">
  <id>https://wykop.pl/</id>
  <title>Wykop</title>
  <link href="https://wykop.pl/" rel="alternate"/>
  <icon>{explicit}</icon>
</feed>
""",
                encoding="utf-8",
            )

            normalize_feed_self_links(feeds_dir)
            first = feed.read_text(encoding="utf-8")
            icon = _tag_value(first, "icon")
            logo = _tag_value(first, "logo")
            icon_query = parse_qs(urlsplit(icon).query)
            logo_query = parse_qs(urlsplit(logo).query)

            self.assertEqual(icon_query["domain"], ["wykop.pl"])
            self.assertEqual(icon_query["url"], [explicit])
            self.assertEqual(icon_query["sz"], ["64"])
            self.assertEqual(logo_query["url"], [explicit])
            self.assertEqual(logo_query["sz"], ["256"])

            changed = normalize_feed_self_links(feeds_dir)
            self.assertEqual(changed, [])
            self.assertEqual(feed.read_text(encoding="utf-8"), first)

    def test_managed_icon_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            feeds_dir = Path(tmp)
            feed = feeds_dir / "feed_ubuntu.xml"
            feed.write_text(
                """<feed xmlns="http://www.w3.org/2005/Atom">
  <id>https://ubuntu.com/blog</id>
  <title>Ubuntu</title>
  <link href="https://ubuntu.com/blog" rel="alternate"/>
  <icon>https://feeds.trfny.com/favicon?domain=ubuntu.com&amp;sz=64</icon>
  <logo>https://feeds.trfny.com/favicon?domain=ubuntu.com&amp;sz=256</logo>
</feed>
""",
                encoding="utf-8",
            )

            changed = normalize_feed_self_links(feeds_dir)

            self.assertEqual(changed, [])

    def test_json_sidecar_item_urls_are_not_rebuilt(self):
        with tempfile.TemporaryDirectory() as tmp:
            feeds_dir = Path(tmp)
            feed = feeds_dir / "feed_weather.xml"
            sidecar = feeds_dir / "feed_weather.json"
            feed.write_text(
                """<feed xmlns="http://www.w3.org/2005/Atom">
  <id>https://weather.trfny.com/</id>
  <title>Weather</title>
  <link href="https://weather.trfny.com/" rel="alternate"/>
  <icon>https://weather.trfny.com/favicon.ico</icon>
</feed>
""",
                encoding="utf-8",
            )
            sidecar.write_text(
                json.dumps(
                    {
                        "version": "https://jsonfeed.org/version/1.1",
                        "title": "Weather",
                        "favicon": "https://weather.trfny.com/favicon.ico",
                        "icon": "https://weather.trfny.com/favicon.ico",
                        "items": [
                            {
                                "id": "tag:weather,2026:entry",
                                "url": "tag:weather,2026:entry",
                                "title": "Forecast",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            normalize_feed_self_links(feeds_dir)
            payload = json.loads(sidecar.read_text(encoding="utf-8"))

            self.assertTrue(payload["favicon"].startswith(FAVICON_PROXY_ORIGIN))
            self.assertTrue(payload["icon"].startswith(FAVICON_PROXY_ORIGIN))
            self.assertEqual(payload["items"][0]["url"], "tag:weather,2026:entry")

    def test_regenerates_existing_json_sidecar_from_normalized_xml(self):
        with tempfile.TemporaryDirectory() as tmp:
            feeds_dir = Path(tmp)
            feed = feeds_dir / "feed_example.xml"
            sidecar = feeds_dir / "feed_example.json"
            feed.write_text(
                """<feed xmlns="http://www.w3.org/2005/Atom">
  <id>https://example.com/</id>
  <title>Example</title>
  <link href="https://example.com/news" rel="alternate"/>
  <icon>https://example.com/favicon.ico</icon>
  <entry>
    <id>https://example.com/a</id>
    <title>A</title>
    <link href="https://example.com/a" rel="alternate"/>
    <updated>2026-10-03T12:00:00+00:00</updated>
    <content>Hello</content>
  </entry>
</feed>
""",
                encoding="utf-8",
            )
            sidecar.write_text(
                json.dumps(
                    {
                        "version": "https://jsonfeed.org/version/1.1",
                        "title": "Example",
                        "favicon": "https://example.com/favicon.ico",
                        "icon": "https://example.com/favicon.ico",
                        "items": [
                            {
                                "id": "https://example.com/a",
                                "url": "https://example.com/a",
                                "title": "A",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            changed = normalize_feed_self_links(feeds_dir)
            payload = json.loads(sidecar.read_text(encoding="utf-8"))

            self.assertEqual(changed, [feed])
            self.assertTrue(payload["favicon"].startswith(FAVICON_PROXY_ORIGIN))
            self.assertTrue(payload["icon"].startswith(FAVICON_PROXY_ORIGIN))
            self.assertEqual(
                parse_qs(urlsplit(payload["favicon"]).query)["sz"],
                ["64"],
            )
            self.assertEqual(parse_qs(urlsplit(payload["icon"]).query)["sz"], ["256"])
            self.assertEqual(payload["items"][0]["url"], "https://example.com/a")


if __name__ == "__main__":
    unittest.main()
