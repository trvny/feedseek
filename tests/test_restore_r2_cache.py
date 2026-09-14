import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import restore_r2_cache


class RestoreR2CacheTests(unittest.TestCase):
    def test_missing_object_errors_are_distinguished_from_transport_failures(self):
        self.assertTrue(restore_r2_cache.is_missing_object_error("NoSuchKey"))
        self.assertTrue(
            restore_r2_cache.is_missing_object_error(
                "The specified key does not exist."
            )
        )
        self.assertFalse(restore_r2_cache.is_missing_object_error("HTTP 503 timeout"))

    def test_default_contract_matches_feedseek_r2_storage(self):
        self.assertEqual(restore_r2_cache.DEFAULT_BUCKET, "feedseek-cache")
        self.assertEqual(restore_r2_cache.DEFAULT_KEY, "snapshots/cache.tar.gz")


class AuthoritativeRestoreTests(unittest.TestCase):
    def test_restored_snapshot_replaces_stale_local_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            restored = root / "restored"
            target = root / "cache"
            restored.mkdir()
            target.mkdir()
            (restored / "jbzd_posts.json").write_text("new", encoding="utf-8")
            (target / "jbzd_posts.json").write_text("old", encoding="utf-8")
            (target / "stale_only.json").write_text("stale", encoding="utf-8")

            restore_r2_cache.replace_cache_tree(restored, target)

            self.assertEqual((target / "jbzd_posts.json").read_text(), "new")
            self.assertFalse((target / "stale_only.json").exists())


if __name__ == "__main__":
    unittest.main()
