import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class MakefileCacheTests(unittest.TestCase):
    def test_incremental_targets_restore_r2_inside_each_recipe(self):
        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

        self.assertIn(".NOTPARALLEL:", makefile)
        self.assertIn("define RESTORE_CACHE", makefile)
        self.assertIn("tools/restore_r2_cache.py", makefile)
        self.assertNotIn("feeds: cache-restore", makefile)
        self.assertNotIn("feed: cache-restore", makefile)
        self.assertNotIn("feeds_%: cache-restore", makefile)
        self.assertNotIn("feeds_beatport: cache-restore", makefile)
        self.assertNotIn("feeds_windows11_release_notes: cache-restore", makefile)

        sections = (
            makefile.split(".PHONY: feeds\n", 1)[1].split(".PHONY: feeds-full", 1)[0],
            makefile.split(".PHONY: feed\n", 1)[1].split(".PHONY: feed-full", 1)[0],
            makefile.split("feeds_%:", 1)[1].split("FULL_FEEDS :=", 1)[0],
            makefile.split(".PHONY: feeds_beatport", 1)[1].split(".PHONY: feeds_windows11_release_notes", 1)[0],
            makefile.split(".PHONY: feeds_windows11_release_notes", 1)[1].split(".PHONY: feeds_commoninja", 1)[0],
        )
        for section in sections:
            self.assertIn("$(RESTORE_CACHE)", section)

    def test_multiple_incremental_goals_each_get_a_restore(self):
        result = subprocess.run(
            ["make", "-n", "feeds_trojka", "feeds_czworka"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.count("tools/restore_r2_cache.py"), 2)

    def test_full_and_commoninja_targets_stay_cache_independent(self):
        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
        self.assertNotIn("feeds-full: cache-restore", makefile)
        self.assertNotIn("feed-full: cache-restore", makefile)
        commoninja = makefile.split(".PHONY: feeds_commoninja", 1)[1].split(".PHONY: validate", 1)[0]
        self.assertIn("feed_generators/commoninja.py --full", commoninja)
        self.assertNotIn("RESTORE_CACHE", commoninja)
        self.assertNotIn("tools/backup_r2_cache.py", commoninja)


if __name__ == "__main__":
    unittest.main()
