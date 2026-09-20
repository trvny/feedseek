import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import restore_r2_cache


class RestoreR2CacheTests(unittest.TestCase):
    def test_missing_object_errors_are_distinguished_from_transport_failures(self):
        self.assertTrue(restore_r2_cache.is_missing_object_error("NoSuchKey"))
        self.assertTrue(restore_r2_cache.is_missing_object_error("The specified key does not exist."))
        self.assertFalse(restore_r2_cache.is_missing_object_error("HTTP 503 timeout"))

    def test_default_contract_matches_feedseek_r2_storage(self):
        self.assertEqual(restore_r2_cache.DEFAULT_BUCKET, "feedseek-cache")
        self.assertEqual(restore_r2_cache.DEFAULT_KEY, "snapshots/cache.tar.gz")

    def test_failed_restore_clears_stale_authorization_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "cache"
            target.mkdir()
            marker = target / restore_r2_cache.CACHE_MARKER
            marker.write_text("stale\n", encoding="utf-8")
            with mock.patch.object(restore_r2_cache, "_fetch_archive", return_value=False):
                restored = restore_r2_cache.restore_from_r2("bucket", "key", target)
            self.assertFalse(restored)
            self.assertFalse(marker.exists())


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

    def test_registry_declares_molt_cache_rename(self):
        migrations = restore_r2_cache.cache_file_migrations()
        self.assertEqual(migrations["moltbook_posts.json"], "molt_posts.json")

    def test_cache_rename_updates_file_and_manifest_without_rewriting_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp)
            payload = '{"entries":[{"entry_id":"legacy-id","link":"https://example.com"}]}'
            legacy = cache / "moltbook_posts.json"
            legacy.write_text(payload, encoding="utf-8")
            (cache / restore_r2_cache.SNAPSHOT_MANIFEST).write_text(
                '{"version": 1, "files": ["moltbook_posts.json"]}', encoding="utf-8"
            )

            restore_r2_cache.apply_cache_file_migrations(
                cache, {"moltbook_posts.json": "molt_posts.json"}
            )

            current = cache / "molt_posts.json"
            self.assertFalse(legacy.exists())
            self.assertEqual(current.read_text(encoding="utf-8"), payload)
            self.assertEqual(
                restore_r2_cache._read_snapshot_manifest(cache), {"molt_posts.json"}
            )

    def test_previous_manifest_allows_a_new_stateful_feed_to_bootstrap(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp)
            (cache / "old_posts.json").write_text('{"entries": [{"id": "old"}]}', encoding="utf-8")
            (cache / restore_r2_cache.SNAPSHOT_MANIFEST).write_text(
                '{"version": 1, "files": ["old_posts.json"]}', encoding="utf-8"
            )
            restore_r2_cache.validate_cache_snapshot(cache, {"old_posts.json", "new_posts.json"})

    def test_manifest_writer_keeps_previous_state_when_new_feed_failed(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp)
            (cache / "old_posts.json").write_text('{"entries": [{"id": "old"}]}', encoding="utf-8")
            (cache / restore_r2_cache.SNAPSHOT_MANIFEST).write_text(
                '{"version": 1, "files": ["old_posts.json"]}', encoding="utf-8"
            )
            restore_r2_cache.write_cache_manifest(cache, {"old_posts.json", "new_posts.json"})
            manifest = restore_r2_cache._read_snapshot_manifest(cache)
            self.assertEqual(manifest, {"old_posts.json"})

    def test_manifest_writer_adds_new_cache_after_successful_first_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp)
            for name in ("old_posts.json", "new_posts.json"):
                (cache / name).write_text('{"entries": [{"id": "ok"}]}', encoding="utf-8")
            (cache / restore_r2_cache.SNAPSHOT_MANIFEST).write_text(
                '{"version": 1, "files": ["old_posts.json"]}', encoding="utf-8"
            )
            restore_r2_cache.write_cache_manifest(cache, {"old_posts.json", "new_posts.json"})
            manifest = restore_r2_cache._read_snapshot_manifest(cache)
            self.assertEqual(manifest, {"old_posts.json", "new_posts.json"})

    def test_manifest_writer_still_requires_previous_established_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp)
            (cache / restore_r2_cache.SNAPSHOT_MANIFEST).write_text(
                '{"version": 1, "files": ["old_posts.json"]}', encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "missing required cache"):
                restore_r2_cache.write_cache_manifest(cache, {"old_posts.json", "new_posts.json"})


class SnapshotValidationTests(unittest.TestCase):
    def test_required_cache_file_must_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp)
            with self.assertRaisesRegex(ValueError, "missing required cache"):
                restore_r2_cache.validate_cache_snapshot(cache, {"daily_quote_posts.json"})

    def test_every_json_cache_must_be_parseable_and_usable(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp)
            (cache / "daily_quote_posts.json").write_text("{not json", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid cache JSON"):
                restore_r2_cache.validate_cache_snapshot(cache, {"daily_quote_posts.json"})


if __name__ == "__main__":
    unittest.main()
