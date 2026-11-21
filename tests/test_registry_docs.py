import re
import unittest
from pathlib import Path

import yaml


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
FEEDSEEK = ROOT


def load_registry():
    data = yaml.safe_load((FEEDSEEK / "feeds.yaml").read_text(encoding="utf-8"))
    return data["feeds"]


class RegistryDocsTests(unittest.TestCase):
    def test_every_registered_feed_has_a_generator_and_readme_row(self):
        registry = load_registry()
        missing_scripts = sorted(
            name
            for name, config in registry.items()
            if not (FEEDSEEK / "feed_generators" / config["script"]).is_file()
        )
        self.assertEqual(missing_scripts, [])

        readme = (FEEDSEEK / "README.md").read_text(encoding="utf-8")
        documented = set(re.findall(r"(?:github\.io/feedseek/|`)([A-Za-z0-9_-]+)\.xml", readme))
        public = {config.get("public_name") or key for key, config in registry.items()}
        self.assertEqual(documented, public)

        for name, config in registry.items():
            public_name = config.get("public_name") or name
            raw_url = f"https://trvny.github.io/feedseek/{public_name}.xml"
            if config.get("enabled", True):
                self.assertIn(raw_url, readme)
            else:
                self.assertNotIn(raw_url, readme)

    def test_protected_feed_public_names_stay_equal_to_registry_keys(self):
        registry = load_registry()
        for key in ("beatport_top100", "daily_digest", "daily_quote", "wikipedia_pl"):
            with self.subTest(key=key):
                self.assertEqual(registry[key].get("public_name", key), key)

    def test_readme_feed_counts_match_registry(self):
        expected = len(load_registry())
        english = (FEEDSEEK / "README.md").read_text(encoding="utf-8")
        polish = (FEEDSEEK / "README_pl.md").read_text(encoding="utf-8")
        chinese = (FEEDSEEK / "README_zh.md").read_text(encoding="utf-8")

        def count(pattern: str, text: str, label: str) -> int:
            match = re.search(pattern, text)
            self.assertIsNotNone(match, f"missing {label} feed count")
            return int(match.group(1))

        counts = [
            count(r"feeds-(\d+)-d6541a", english, "English badge"),
            count(r"feeds-(\d+)-d6541a", polish, "Polish badge"),
            count(r"feeds-(\d+)-d6541a", chinese, "Chinese badge"),
            count(r"feeds\.yaml \((\d+) źródeł\)", polish, "Polish registry marker"),
        ]
        self.assertEqual(counts, [expected] * len(counts))

    def test_public_feed_list_only_references_registered_feeds(self):
        data = yaml.safe_load((FEEDSEEK / "feeds.yaml").read_text(encoding="utf-8"))
        registry = set(data["feeds"])
        published = [
            item if isinstance(item, str) else item["name"]
            for item in data["published_feeds"]
        ]

        self.assertEqual(len(published), len(set(published)))
        self.assertEqual(sorted(set(published) - registry), [])


if __name__ == "__main__":
    unittest.main()
