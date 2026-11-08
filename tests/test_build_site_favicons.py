import html
import importlib.util
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "site" / "build_site.py"
SPEC = importlib.util.spec_from_file_location("build_site", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load {MODULE_PATH}")
build_site = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_site)


class SiteFaviconTests(unittest.TestCase):
    def _parse(self, xml):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "feed_test.xml"
            path.write_text(xml, encoding="utf-8")
            return build_site.parse_feed(path)

    def test_atom_icon_and_logo_are_read(self):
        feed = self._parse(
            """<?xml version="1.0"?>
            <feed xmlns="http://www.w3.org/2005/Atom">
              <title>Test</title>
              <link rel="alternate" href="https://example.com/news"/>
              <icon>https://example.com/icon.png</icon>
              <logo>/logo.svg</logo>
            </feed>
            """
        )

        self.assertEqual(feed["icon"], "https://example.com/icon.png")
        self.assertEqual(feed["logo"], "/logo.svg")

    def test_rss_channel_image_is_read(self):
        feed = self._parse(
            """<?xml version="1.0"?>
            <rss version="2.0"><channel>
              <title>Test</title>
              <link>https://example.com/</link>
              <description>Test feed</description>
              <image><url>https://example.com/rss.png</url></image>
            </channel></rss>
            """
        )

        self.assertEqual(feed["icon"], "https://example.com/rss.png")

    def test_relative_rss_icon_resolves_against_source(self):
        feed = self._parse(
            """<?xml version="1.0"?>
            <rss version="2.0"><channel>
              <title>Test</title>
              <link>https://example.com/news/</link>
              <description>Test feed</description>
              <image><url>icons/favicon.png</url></image>
            </channel></rss>
            """
        )

        self.assertEqual(
            feed["icon"],
            "https://example.com/news/icons/favicon.png",
        )

    def test_feed_icon_precedes_service_fallbacks(self):
        candidates = build_site.favicon_candidates(
            {
                "source": "https://trojka.polskieradio.pl/news",
                "icon": "https://trojka.polskieradio.pl/assets/favicon-32x32.png",
                "logo": "https://trojka.polskieradio.pl/logo.svg",
            }
        )

        self.assertEqual(
            candidates[0],
            "https://trojka.polskieradio.pl/assets/favicon-32x32.png",
        )
        self.assertIn(
            build_site.favicon_proxy("trojka.polskieradio.pl", sz=64),
            candidates,
        )
        self.assertEqual(candidates[-1], build_site.FAVICON_SVG)

    def test_old_third_party_icon_is_demoted_behind_managed_resolver(self):
        old_google = "https://www.google.com/s2/favicons?domain=usa.gov&sz=64"
        candidates = build_site.favicon_candidates(
            {
                "source": "https://www.usa.gov/",
                "icon": old_google,
                "logo": "",
            }
        )

        self.assertEqual(candidates[0], build_site.favicon_proxy("usa.gov", sz=64))
        self.assertIn(old_google, candidates)
        self.assertEqual(candidates[-1], build_site.FAVICON_SVG)

    def test_root_favicon_guess_is_demoted_behind_managed_resolver(self):
        candidates = build_site.favicon_candidates(
            {
                "source": "https://newsify.today/polish/PL",
                "icon": "https://newsify.today/favicon.ico",
                "logo": "https://newsify.today/favicon.ico",
            }
        )

        self.assertEqual(
            candidates[0],
            build_site.favicon_proxy("newsify.today", sz=64),
        )
        self.assertIn("https://newsify.today/favicon.ico", candidates)

    def test_rendered_card_embeds_remaining_fallbacks(self):
        card = build_site.render_card(
            {
                "filename": "feed_test.xml",
                "title": "Test",
                "subtitle": "",
                "source": "https://example.com/",
                "icon": "https://example.com/icon.png",
                "logo": "",
                "entries": 1,
                "updated": None,
            },
            "https://feeds.example/",
        )

        marker = 'data-fallbacks="'
        start = card.index(marker) + len(marker)
        encoded = card[start : card.index('"', start)]
        fallbacks = json.loads(html.unescape(encoded))
        self.assertIn(build_site.favicon_proxy("example.com", sz=64), fallbacks)
        self.assertEqual(fallbacks[-1], build_site.FAVICON_SVG)

    def test_rendered_card_has_expandable_description_viewport(self):
        card = build_site.render_card(
            {
                "filename": "feed_long_test.xml",
                "title": "Long Test",
                "subtitle": "A deliberately long description " * 20,
                "source": "https://example.com/",
                "icon": "",
                "logo": "",
                "entries": 1,
                "updated": None,
            },
            "https://feeds.example/",
        )

        self.assertIn('class="card__desc"', card)
        self.assertIn('id="desc-feed_long_test.xml"', card)
        self.assertIn('data-expand-desc', card)
        self.assertIn('aria-controls="desc-feed_long_test.xml"', card)
        self.assertIn('tabindex="-1"', card)

    def test_index_expands_long_descriptions_without_unbounded_card_growth(self):
        rendered = build_site.build_index([], "https://feeds.example/")
        self.assertIn("max-height: 4.35em", rendered)
        self.assertIn("max-height: 8.7em", rendered)
        self.assertIn("overflow-y: auto", rendered)
        self.assertIn("text.scrollHeight > text.clientHeight + 1", rendered)
        self.assertIn("expand.textContent = expanded ? 'less' : 'more…'", rendered)
        self.assertIn("requestAnimationFrame(refreshDescriptionToggles)", rendered)
        self.assertIn("text.tabIndex = expanded ? 0 : -1", rendered)
        self.assertIn("text.focus({ preventScroll: true })", rendered)

    def test_autodiscovery_advertises_xml_and_json_feed(self):
        links = build_site.render_autodiscovery(
            [{"filename": "feed_test.xml", "title": "Test", "format": "atom"}],
            "https://feeds.example/",
        )

        self.assertIn('type="application/atom+xml"', links)
        self.assertIn('href="https://feeds.example/test.xml"', links)
        self.assertIn('type="application/json"', links)
        self.assertIn('href="https://feeds.example/test.json"', links)

    def test_model_catalog_uses_only_existing_feed_urls_and_normalized_metadata(self):
        feeds = [
            {
                "filename": "feed_alpha.xml",
                "title": "Alpha",
                "subtitle": "Plaintext headlines",
                "source": "https://source.example/news",
                "entries": 2,
                "updated": datetime(2026, 10, 25, 20, 30, tzinfo=timezone.utc),
            },
            {
                "filename": "feed_beta.xml",
                "title": "Béta",
                "subtitle": "",
                "source": "",
                "entries": 0,
                "updated": None,
            },
        ]
        result = json.loads(
            build_site.build_model_feed_catalog(feeds, "https://trvny.github.io/feedseek/")
        )
        self.assertEqual(result["format"], "feedseek-model-feed-catalog")
        self.assertEqual(result["version"], 1)
        self.assertEqual(result["feed_count"], 2)
        self.assertEqual(result["site_url"], "https://trvny.github.io/feedseek/")
        self.assertEqual([entry["key"] for entry in result["feeds"]], ["alpha", "beta"])
        self.assertEqual(
            result["feeds"][0]["model_feed_url"],
            "https://trvny.github.io/feedseek/alpha.json",
        )
        self.assertEqual(
            result["feeds"][0]["feed_url"],
            "https://trvny.github.io/feedseek/alpha.xml",
        )
        self.assertEqual(result["feeds"][0]["entry_count"], 2)
        self.assertEqual(result["feeds"][0]["updated_at"], "2026-10-25T20:30:00Z")
        self.assertEqual(result["feeds"][1]["updated_at"], None)
        self.assertEqual(result["feeds"][1]["title"], "Béta")
        self.assertNotIn("items", result["feeds"][0])  # No second content store.

    def test_sitemap_lists_html_pages_without_lastmod(self):
        base = "https://trvny.github.io/feedseek/"
        root = ET.fromstring(build_site.build_sitemap(base))
        urls = root.findall("{*}url")
        self.assertEqual([url.findtext("{*}loc") for url in urls], [base, base + "reader/"])
        self.assertFalse(root.findall(".//{*}lastmod"), "Rebuild dates are not verified content changes")

    def test_machine_discovery_lists_catalog_and_model_json_urls(self):
        feeds = [{
            "filename": "feed_alpha.xml",
            "title": "Alpha",
            "subtitle": "Test source",
            "source": "https://source.example/",
            "updated": datetime(2026, 10, 25, tzinfo=timezone.utc),
            "entries": 3,
            "icon": "",
            "logo": "",
            "format": "atom",
        }]
        base = "https://feeds.example/"
        index = build_site.build_index(feeds, base)
        self.assertIn('href="https://feeds.example/model-feeds.json"', index)
        self.assertIn('data-model-feed href="https://feeds.example/alpha.json"', index)
        self.assertIn('href="model-feeds.json"', index)
        llms = build_site.build_llms_txt(feeds, base)
        self.assertIn("[Model Feed catalog (JSON)](https://feeds.example/model-feeds.json)", llms)
        self.assertIn("https://feeds.example/alpha.json", llms)
        self.assertIn("model-feeds.json", build_site.build_index_markdown(feeds, base))
        self.assertIn("model-feeds.json", build_site.build_llms_full(feeds, base))
        webmcp = (MODULE_PATH.parent / "webmcp.js").read_text(encoding="utf-8")
        self.assertIn('modelFeedUrl: card.querySelector(".card__actions a[data-model-feed]")', webmcp)

    def test_llms_full_links_dedicated_model_feed(self):
        feed = {
            "filename": "feed_test.xml",
            "title": "Test",
            "subtitle": "Test feed",
            "source": "https://example.com/",
        }
        rendered = build_site.build_llms_full([feed], "https://feeds.example/")
        self.assertIn(
            "- LLM-friendly JSON Model Feed: https://feeds.example/test.json",
            rendered,
        )

    def test_markdown_metadata_is_flattened_and_escaped(self):
        feed = {
            "filename": "feed_test.xml",
            "title": "Safe](https://evil.example)\n# injected",
            "subtitle": "first line\n## injected",
            "source": "https://example.com/",
        }
        rendered = build_site.build_index_markdown([feed], "https://feeds.example/")
        self.assertIn(r"Safe\]\(https://evil.example\) # injected", rendered)
        self.assertNotIn("\n## injected", rendered)

    def test_reader_metadata_uses_build_base(self):
        rendered = build_site.build_reader_html("https://feedseek.pages.dev/")
        self.assertIn("https://feedseek.pages.dev/reader/", rendered)
        self.assertNotIn("https://trvny.github.io/feedseek/reader/", rendered)

    def test_index_advertises_llms_alternate(self):
        rendered = build_site.build_index([], "https://feeds.example/")
        self.assertIn(
            'rel="alternate" type="text/plain" href="https://feeds.example/llms.txt"',
            rendered,
        )

    def test_sitemap_includes_reader_and_directory(self):
        rendered = build_site.build_sitemap("https://trvny.github.io/feedseek/")
        self.assertIn("<loc>https://trvny.github.io/feedseek/</loc>", rendered)
        self.assertIn("<loc>https://trvny.github.io/feedseek/reader/</loc>", rendered)
        self.assertNotIn("https://trfny.com/", rendered)

    def test_website_schema_uses_durable_hub_identity(self):
        rendered = build_site.build_index([], "https://trvny.github.io/feedseek/")
        self.assertIn("https://travny.pages.dev/#creator", rendered)
        self.assertIn("https://travny.pages.dev/#website", rendered)
        self.assertIn('href="https://travny.pages.dev/"', rendered)
        self.assertNotIn('href="https://trfny.com/"', rendered)

    def test_directory_explains_feeds_without_javascript(self):
        rendered = build_site.build_index([], "https://trvny.github.io/feedseek/")
        self.assertIn('<details class="answer-guide" id="about-feedseek">', rendered)
        self.assertIn("What does Feedseek publish?", rendered)
        self.assertIn("Model Feed", rendered)
        self.assertIn("How often are the feeds updated?", rendered)
        self.assertIn('href="subscriptions.opml"', rendered)
        self.assertIn('href="reader/"', rendered)
        self.assertNotIn('"@type":"FAQPage"', rendered)

    def test_robots_publish_content_signal(self):
        rendered = build_site.build_robots("https://feeds.example/")
        self.assertIn(
            "Content-Signal: ai-train=yes, search=yes, ai-input=yes",
            rendered,
        )
        self.assertIn("Sitemap: https://feeds.example/sitemap.xml", rendered)
        for agent in ("OAI-SearchBot", "Claude-SearchBot", "PerplexityBot"):
            self.assertIn(f"User-agent: {agent}", rendered)

    def test_publication_requires_json_sidecar(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            xml = directory / "feed_test.xml"
            xml.write_text("<feed />", encoding="utf-8")
            original = build_site.FEEDS_DIR
            build_site.FEEDS_DIR = directory
            self.addCleanup(setattr, build_site, "FEEDS_DIR", original)

            with self.assertRaisesRegex(SystemExit, "feed_test.json"):
                build_site.require_model_sidecars(
                    [{"filename": "feed_test.xml", "title": "Test"}]
                )

    def test_publication_accepts_xml_json_pair(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / "feed_test.xml").write_text("<feed />", encoding="utf-8")
            (directory / "feed_test.json").write_text(json.dumps({"format": "feedseek-model-feed", "version": 1, "title": "Test", "items": []}), encoding="utf-8")
            original = build_site.FEEDS_DIR
            build_site.FEEDS_DIR = directory
            self.addCleanup(setattr, build_site, "FEEDS_DIR", original)

            build_site.require_model_sidecars(
                [{"filename": "feed_test.xml", "title": "Test"}]
            )



class FullPublicationTests(unittest.TestCase):
    def test_all_feeds_keep_curated_order_then_add_unselected_by_title(self):
        with tempfile.TemporaryDirectory() as tmp:
            feed_dir = Path(tmp)
            for name, title in (("alpha", "Alpha"), ("zed", "Zed"), ("beta", "Beta")):
                (feed_dir / f"feed_{name}.xml").write_text(
                    '<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom">'
                    f"<title>{title}</title></feed>",
                    encoding="utf-8",
                )
            original = build_site.FEEDS_DIR
            build_site.FEEDS_DIR = feed_dir
            try:
                selected = [build_site.parse_feed(feed_dir / "feed_zed.xml")]
                result = build_site.collect_all_feeds(selected)
            finally:
                build_site.FEEDS_DIR = original

        self.assertEqual(
            [f["filename"] for f in result],
            ["feed_zed.xml", "feed_alpha.xml", "feed_beta.xml"],
        )
        self.assertIs(result[0], selected[0])


class LiveFeedMetadataTests(unittest.TestCase):
    def test_canonical_pages_self_link_rebases_onto_other_site_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "feed_demo.xml"
            source.write_text(
                f'<feed><link href="{build_site.PUBLIC_BASE}demo.xml" rel="self"/></feed>',
                encoding="utf-8",
            )
            source.with_suffix(".json").write_text('{"format":"feedseek-model-feed"}', encoding="utf-8")
            out = root / "public"
            out.mkdir()
            build_site.copy_public_feed_pair(source, out, "https://feeds.example/")
            self.assertIn('href="https://feeds.example/demo.xml" rel="self"', (out / "demo.xml").read_text(encoding="utf-8"))

    def test_pages_self_urls_are_live_and_git_files_remain_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            feed_dir = root / "feeds"
            public = root / "public"
            feed_dir.mkdir()
            public.mkdir()
            source = feed_dir / "feed_test.xml"
            raw = (
                f"https://raw.githubusercontent.com/{build_site.REPO_SLUG}"
                "/main/feeds/feed_test.xml"
            )
            xml = f"""<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <link href="{raw}" rel="self"/>
</feed>
"""
            source.write_text(xml, encoding="utf-8")
            model = {
                "format": "feedseek-model-feed",
                "version": 1,
                "feed_url": raw.replace(".xml", ".json"),
                "source_feed": raw,
                "items": [{"id": "one", "text": "Some text"}],
            }
            sibling = source.with_suffix(".json")
            raw_json = json.dumps(model)
            sibling.write_text(raw_json, encoding="utf-8")
            base = "https://trvny.github.io/feedseek/"

            build_site.copy_public_feed_pair(source, public, base)

            self.assertEqual(source.read_text(encoding="utf-8"), xml)
            self.assertEqual(sibling.read_text(encoding="utf-8"), raw_json)
            staged = (public / source.name).read_text(encoding="utf-8")
            self.assertIn(f'href="{base}test.xml" rel="self"', staged)
            self.assertNotIn(raw, staged)
            legacy = (public / "feed_test.xml").read_text(encoding="utf-8")
            self.assertEqual(legacy, (public / "test.xml").read_text(encoding="utf-8"))
            staged_json = json.loads((public / "test.json").read_text(encoding="utf-8"))
            self.assertTrue((public / "feed_test.json").is_file())
            self.assertEqual(staged_json["feed_url"], base + "test.json")
            self.assertEqual(staged_json["source_feed"], base + "test.xml")
            self.assertEqual(staged_json["items"], model["items"])

    def test_self_link_attribute_order_can_be_reversed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "feed_test.xml"
            raw = (
                f"https://raw.githubusercontent.com/{build_site.REPO_SLUG}"
                "/main/feeds/feed_test.xml"
            )
            source.write_text(
                f'<feed><link rel="self" href="{raw}"/></feed>', encoding="utf-8"
            )
            source.with_suffix(".json").write_text("{}", encoding="utf-8")
            public = root / "public"
            public.mkdir()

            build_site.copy_public_feed_pair(source, public, "https://example.test/live/")

            self.assertIn(
                'rel="self" href="https://example.test/live/test.xml"',
                (public / source.name).read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
