import datetime
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))

import fourchan  # noqa: E402


class FourchanCapTests(unittest.TestCase):
    def test_curated_nsfw_boards_are_admitted_and_visible_in_docs(self):
        self.assertIn("b", fourchan.NSFW_BOARD_CODES)
        self.assertIn("h", fourchan.NSFW_BOARD_CODES)
        self.assertIn("gif", fourchan.NSFW_BOARD_CODES)
        self.assertTrue(fourchan.NSFW_BOARD_CODES)
        self.assertEqual(len(set(board for board, _ in fourchan.BOARDS)), len(fourchan.BOARDS))
        self.assertTrue(
            all("[NSFW]" in label for board, label in fourchan.BOARDS
                if board in fourchan.NSFW_BOARD_CODES)
        )
        sources = fourchan.doc_sources()
        self.assertTrue(any(label.startswith("/h/") for label, _ in sources))
        self.assertTrue(all(fourchan.BOARDS_BASE in url for _, url in sources))

    def test_nsfw_threads_are_labelled_and_still_text_only(self):
        payload = [{"threads": [{
            "no": 123, "sub": "A headline",
            "com": "<p>Body with <b>markup</b><img src='https://example.test/p.png'></p>",
            "time": 1_790_000_000,
        }]}]
        response = Mock()
        response.json.return_value = payload
        with patch.object(fourchan.requests, "get", return_value=response), patch.object(
            fourchan.time, "sleep"
        ):
            entries = fourchan.scrape_board("h", "/h/ Hentai [NSFW]", set())
        self.assertEqual(len(entries), 1)
        self.assertTrue(entries[0]["title"].startswith("[NSFW] /h/"))
        self.assertEqual(entries[0]["description"], "Body with markup")
        self.assertNotIn("<img", entries[0]["description"])
        self.assertTrue(fourchan._keep_allowed_source(entries[0]))
        self.assertEqual(entries[0]["date"].tzinfo, datetime.UTC)

    def test_main_sets_hard_per_source_publication_cap(self):
        with patch.object(fourchan, "run", return_value=True) as mocked_run:
            self.assertTrue(fourchan.main())

        kwargs = mocked_run.call_args.kwargs
        self.assertEqual(kwargs["per_source_cap"], {"": 20})
        self.assertEqual(kwargs["max_entries"], 200)


if __name__ == "__main__":
    unittest.main()
