import unittest
from pathlib import Path


class MakefileCacheTests(unittest.TestCase):
    def test_incremental_targets_restore_r2_for_every_run(self):
        makefile = (Path(__file__).resolve().parents[1] / "Makefile").read_text(
            encoding="utf-8"
        )

        self.assertIn("cache-restore:", makefile)
        self.assertNotIn("cache-ready:", makefile)
        self.assertIn("feeds: cache-restore", makefile)
        self.assertIn("feed: cache-restore", makefile)
        self.assertIn("feeds_%: cache-restore FORCE", makefile)
        self.assertIn("feeds_beatport: cache-restore", makefile)
        self.assertIn("feeds_windows11_release_notes: cache-restore", makefile)
        self.assertIn("feeds_commoninja: cache-restore", makefile)
        commoninja = makefile.split("feeds_commoninja: cache-restore", 1)[1].split(".PHONY: validate", 1)[0]
        self.assertNotIn("rm -f cache/.r2-restored", commoninja)
        self.assertIn("tools/restore_r2_cache.py", makefile)

        self.assertNotIn("feeds-full: cache-restore", makefile)
        self.assertNotIn("feed-full: cache-restore", makefile)


if __name__ == "__main__":
    unittest.main()
