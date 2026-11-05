import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))
import github


class GitHubRequestedSourcesTests(unittest.TestCase):
    def test_requested_beehiiv_feed_is_already_registered(self):
        self.assertIn(
            (github.STAR_HISTORY_NEWSLETTER_LABEL,
             "https://rss.beehiiv.com/feeds/BbNzf9ozGZ.xml", 15),
            github.SOURCES,
        )

    def test_ecosystem_deduplicates_by_url_not_titles(self):
        with patch.object(github, "run", return_value=True) as run:
            self.assertTrue(github.main())
        self.assertIsNone(run.call_args.kwargs["dedupe_title_field"])


if __name__ == "__main__":
    unittest.main()
