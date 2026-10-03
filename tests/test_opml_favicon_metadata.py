import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "site"))

from build_site import build_opml


class OpmlFaviconMetadataTests(unittest.TestCase):
    def test_opml_advertises_feed_icon_through_common_extension_attributes(self):
        feeds = [
            {
                "title": "Example",
                "filename": "feed_example.xml",
                "source": "https://example.com/news",
                "icon": "https://feeds.trfny.com/favicon?domain=example.com&sz=64",
            }
        ]

        rendered = build_opml(feeds, "https://trvny.github.io/feedseek/")

        escaped = (
            "https://feeds.trfny.com/favicon?domain=example.com&amp;sz=64"
        )
        self.assertIn(f'icon="{escaped}"', rendered)
        self.assertIn(f'favicon="{escaped}"', rendered)
        self.assertIn(f'image="{escaped}"', rendered)
        self.assertIn('htmlUrl="https://example.com/news"', rendered)


if __name__ == "__main__":
    unittest.main()
