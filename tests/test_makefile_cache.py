import unittest
from pathlib import Path


class MakefileCacheTests(unittest.TestCase):
    def test_incremental_targets_require_durable_cache_restore(self):
        makefile = (Path(__file__).resolve().parents[1] / "Makefile").read_text(
            encoding="utf-8"
        )

        self.assertIn("cache-ready:", makefile)
        self.assertIn("cache-restore:", makefile)
        self.assertIn("feeds: cache-ready", makefile)
        self.assertIn("feed: cache-ready", makefile)
        self.assertIn("feeds_%: cache-ready FORCE", makefile)
        self.assertIn("tools/restore_r2_cache.py", makefile)

        ready = makefile.split("cache-ready:", 1)[1].split(".PHONY: feeds", 1)[0]
        self.assertIn("*_posts.json", ready)
        clean = makefile.split("clean:", 1)[1]
        self.assertIn("$(CACHE_MARKER)", clean)


if __name__ == "__main__":
    unittest.main()
