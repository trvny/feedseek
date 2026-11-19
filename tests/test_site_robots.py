import importlib.util
import json
import re
import unittest
from pathlib import Path

import feedparser

MODULE_PATH = Path(__file__).resolve().parents[1] / "site" / "build_site.py"
SPEC = importlib.util.spec_from_file_location("build_site", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load {MODULE_PATH}")
build_site = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_site)


class SiteRobotsTests(unittest.TestCase):
    def test_travny_crawler_additions_are_explicitly_allowed(self):
        robots = build_site.build_robots("https://example.com/")
        groups = [block.splitlines() for block in robots.split("\n\n") if block.strip()]
        for agent in (
            "anthropic-ai",
            "BingBot",
            "DuckAssistBot",
            "GPTBot",
            "PerplexityBot",
            "Perplexity-User",
            "KimiBot",
            "Kimi-SearchBot",
            "Kimi-User",
            "Meta-WebIndexer",
            "Meta-ExternalFetcher",
            "Meta-ExternalAgent",
            "Googlebot",
            "Googlebot-News",
            "Googlebot-Image",
            "Googlebot-Video",
            "GoogleOther",
            "GoogleOther-Image",
            "GoogleOther-Video",
            "Google-InspectionTool",
            "DuckDuckBot",
            "YandexBot",
            "YandexFavicons",
            "CCBot",
            "SemanticScholarBot",
            "MistralAI-Index",
            "MistralAI-Training",
            "MistralAI-User",
        ):
            with self.subTest(agent=agent):
                matching = [
                    group
                    for group in groups
                    if any(line.casefold() == f"user-agent: {agent.casefold()}" for line in group)
                ]
                self.assertEqual(len(matching), 1)
                self.assertIn("Allow: /", matching[0])
                self.assertNotIn("Disallow: /", matching[0])
        declared = [
            line.partition(":")[2].strip().casefold()
            for group in groups
            for line in group
            if line.casefold().startswith("user-agent:")
        ]
        self.assertEqual(len(declared), len(set(declared)))
        self.assertIn("User-agent: *\n", robots)
        self.assertIn("Sitemap: https://example.com/sitemap.xml\n", robots)

    def test_sitemap_variants_share_canonical_urls(self):
        """All published formats describe the same pages."""
        base = "https://example.com/feedseek/"
        original = build_site.build_sitemap(base)
        variants = build_site.build_sitemap_variants(build_site.sitemap_urls(base), base)
        urls = [base, base + "reader/"]
        self.assertEqual(
            original,
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"  <url><loc>{base}</loc></url>\n"
            f"  <url><loc>{base}reader/</loc></url>\n"
            "</urlset>\n",
        )
        self.assertEqual(variants["sitemap.txt"].splitlines(), urls)
        self.assertEqual(json.loads(variants["sitemap.json"]), [{"url": url} for url in urls])
        for name, version in (("sitemap-atom.xml", "atom10"), ("sitemap-rss.xml", "rss20")):
            with self.subTest(name=name):
                parsed = feedparser.parse(variants[name].encode("utf-8"))
                self.assertFalse(parsed.bozo)
                self.assertEqual(parsed.version, version)
                self.assertEqual([entry.link for entry in parsed.entries], urls)
        robots = build_site.build_robots(base)
        for name in ("sitemap.txt", "sitemap-atom.xml", "sitemap-rss.xml"):
            self.assertIn(f"Sitemap: {base}{name}\n", robots)
        self.assertNotIn("sitemap.json", robots)

    def test_directory_metadata_describes_curated_feeds_and_agent_access(self):
        """Check directory schema, feed links and agent discovery metadata."""
        base = "https://example.com/feedseek/"
        page = build_site.build_index([], base)
        schema_text = re.search(r'<script type="application/ld\+json">(.*?)</script>', page)
        self.assertIsNotNone(schema_text)
        schema = json.loads(schema_text.group(1))
        self.assertEqual(schema["mainEntity"]["numberOfItems"], 0)
        self.assertEqual(schema["potentialAction"]["target"], base + "reader/")
        self.assertIn("Feedseek | RSS, Atom", page)
        self.assertIn("How can AI agents access Feedseek?", page)
        self.assertIn("every three hours", page)

    def test_invalid_sitemap_urls(self):
        """Reject empty and foreign URLs; reserve feed filenames."""
        base = "https://example.com/feedseek/"
        for urls in ([], ["https://other.example/"]):
            with self.assertRaises(ValueError):
                build_site.build_sitemap_variants(urls, base)
        self.assertTrue({"sitemap-atom", "sitemap-rss"} <= build_site.RESERVED_PUBLIC_STEMS)

    def test_sitemap_url_xml_escaping(self):
        """Feed consumers recover escaped query parameters."""
        base = "https://example.com/"
        url = base + "reader/?a=1&b=2"
        variants = build_site.build_sitemap_variants([url], base)
        for name in ("sitemap-atom.xml", "sitemap-rss.xml"):
            with self.subTest(name=name):
                self.assertIn("a=1&amp;b=2", variants[name])
                parsed = feedparser.parse(variants[name].encode("utf-8"))
                self.assertFalse(parsed.bozo)
                self.assertEqual([entry.link for entry in parsed.entries], [url])


if __name__ == "__main__":
    unittest.main()
