import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("check_registry", ROOT / "tools" / "check_registry.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CheckRegistryTests(unittest.TestCase):
    def tearDown(self):
        MODULE.models.REGISTRY_PATH = ROOT / "feeds.yaml"

    def run_check(self, text: str) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "feeds.yaml"
            path.write_text(text, encoding="utf-8")
            return MODULE.check(path)

    def test_repository_registry_passes(self):
        self.assertEqual(MODULE.check(ROOT / "feeds.yaml"), [])

    def test_yaml_typo_fails(self):
        broken = "feeds:\n  demo:\n  cript: daily_quote.py\n    blog_url: https://example.com/\n"
        self.assertTrue(self.run_check(broken))

    def test_lenient_skip_is_an_error(self):
        errors = self.run_check("feeds:\n  demo:\n    script: missing.py\n    blog_url: https://example.com/\n")
        self.assertIn("invalid feed entry: demo", errors)

    def test_unknown_published_feed_fails(self):
        text = "published_feeds: [nope]\nfeeds:\n  daily_quote:\n    script: daily_quote.py\n    blog_url: https://example.com/\n"
        self.assertTrue(self.run_check(text))


if __name__ == "__main__":
    unittest.main()
