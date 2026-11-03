import importlib.util
import unittest
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


if __name__ == "__main__":
    unittest.main()
