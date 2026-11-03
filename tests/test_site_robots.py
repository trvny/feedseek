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
        for agent in ("anthropic-ai", "BingBot", "DuckAssistBot"):
            with self.subTest(agent=agent):
                self.assertEqual(robots.count(f"User-agent: {agent}\n"), 1)
        self.assertIn("User-agent: *\n", robots)
        self.assertIn("Allow: /\n", robots)
        self.assertIn("Sitemap: https://example.com/sitemap.xml\n", robots)


if __name__ == "__main__":
    unittest.main()
