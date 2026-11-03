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
            "Googlebot",
            "Google-InspectionTool",
            "DuckDuckBot",
            "MistralAI-Index",
            "MistralAI-Training",
            "MistralAI-User",
        ):
            with self.subTest(agent=agent):
                matching = [group for group in groups if f"User-agent: {agent}" in group]
                self.assertEqual(len(matching), 1)
                self.assertIn("Allow: /", matching[0])
                self.assertNotIn("Disallow: /", matching[0])
        self.assertIn("User-agent: *\n", robots)
        self.assertIn("Sitemap: https://example.com/sitemap.xml\n", robots)


if __name__ == "__main__":
    unittest.main()
