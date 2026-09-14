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


class RegistryCacheContractTests(unittest.TestCase):
    def test_weather_is_the_only_active_stateless_feed(self):
        required = restore_r2_cache.required_cache_files()
        self.assertIn("daily_quote_posts.json", required)
        self.assertNotIn("weather_posts.json", required)

    def test_previous_manifest_allows_a_new_stateful_feed_to_bootstrap(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp)
            (cache / "old_posts.json").write_text(
                '{"entries": [{"id": "old"}]}', encoding="utf-8"
            )
            (cache / restore_r2_cache.SNAPSHOT_MANIFEST).write_text(
                '{"version": 1, "files": ["old_posts.json"]}', encoding="utf-8"
            )
            restore_r2_cache.validate_cache_snapshot(
                cache, {"old_posts.json", "new_posts.json"}
            )

    def test_manifest_writer_requires_current_stateful_caches(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp)
            with self.assertRaisesRegex(ValueError, "missing required cache"):
                restore_r2_cache.write_cache_manifest(
                    cache, {"new_posts.json"}
                )



class SnapshotValidationTests(unittest.TestCase):
    def test_required_cache_file_must_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp)
            with self.assertRaisesRegex(ValueError, "missing required cache"):
                restore_r2_cache.validate_cache_snapshot(
                    cache, {"daily_quote_posts.json"}
                )

    def test_every_json_cache_must_be_parseable_and_usable(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp)
            (cache / "daily_quote_posts.json").write_text(
                "{not json", encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "invalid cache JSON"):
                restore_r2_cache.validate_cache_snapshot(
                    cache, {"daily_quote_posts.json"}
                )


if __name__ == "__main__":
    unittest.main()
