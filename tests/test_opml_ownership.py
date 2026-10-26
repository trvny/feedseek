"""Feed Catcher storage cannot overwrite the generated public OPML."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "site"))
import make_opml  # noqa: E402


class OpmlOwnershipTests(unittest.TestCase):
    def test_feed_catcher_storage_is_separate_from_public_catalog(self):
        workflow = (ROOT / ".github" / "workflows" / "add-feed.yml").read_text(encoding="utf-8")
        self.assertIn('Path("site/feed-catcher.opml")', workflow)
        self.assertIn("git add site/feed-catcher.opml", workflow)
        self.assertTrue((ROOT / "site" / "feed-catcher.opml").exists())
        self.assertFalse((ROOT / "site" / "subscriptions.opml").exists())

    def test_refresh_only_writes_public_opml(self):
        from unittest.mock import patch
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "public"
            feeds = [{"title": "Example", "filename": "feed_example.xml", "source": "https://example.com"}]
            with (
                patch.object(make_opml, "OUT_DIR", out),
                patch.object(make_opml, "collect_feeds", return_value=feeds),
                patch.object(make_opml, "site_base_url", return_value="https://example.org/feeds/"),
            ):
                make_opml.main()
            xml = (out / "subscriptions.opml").read_text(encoding="utf-8")
            self.assertIn('xmlUrl="https://example.org/feeds/feed_example.xml"', xml)
            self.assertFalse((Path(tmp) / "site" / "subscriptions.opml").exists())


if __name__ == "__main__":
    unittest.main()
