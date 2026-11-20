"""APIs generator uses the shared native feed pipeline."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))

import apis


class APIsTests(unittest.TestCase):
    @patch("apis.run", return_value=True)
    def test_native_source_and_publication(self, run):
        self.assertTrue(apis.main(full=True))
        options = run.call_args.kwargs
        self.assertEqual(options["feed_name"], "apis")
        self.assertEqual(options["title"], "APIs")
        self.assertEqual(options["blog_url"], "https://publicapis.dev/blog")
        self.assertEqual(options["sources"], [
            ("Public APIs Blog", "https://publicapis.dev/blog/feed.xml", 100),
            ("Public APIs Directory", "https://publicapis.dev/feed.xml", 100),
        ])
        self.assertIsNone(options["dedupe_title_field"])
        self.assertTrue(options["full"])
