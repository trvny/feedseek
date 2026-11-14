import importlib.util
import unittest
import json
import xml.etree.ElementTree as ET
from pathlib import Path

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
        base = "https://example.com/feedseek/"
        original = build_site.build_sitemap(base)
        variants = build_site.build_sitemap_variants(original, base)
        atom = "{http://www.w3.org/2005/Atom}"
        urls = [base, base + "reader/"]
        self.assertEqual(variants["sitemap.txt"].splitlines(), urls)
        self.assertEqual(json.loads(variants["sitemap.json"]), [{"url": url} for url in urls])
        self.assertEqual(
            [link.attrib["href"] for link in ET.fromstring(variants["sitemap-atom.xml"]).findall(f"{atom}entry/{atom}link")],
            urls,
        )
        self.assertEqual(
            [link.text for link in ET.fromstring(variants["sitemap-rss.xml"]).findall("channel/item/link")],
            urls,
        )
        robots = build_site.build_robots(base)
        for name in ("sitemap.txt", "sitemap-atom.xml", "sitemap-rss.xml"):
            self.assertIn(f"Sitemap: {base}{name}\n", robots)
        self.assertNotIn("sitemap.json", robots)


if __name__ == "__main__":
    unittest.main()
