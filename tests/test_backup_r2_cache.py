import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import backup_r2_cache


class BackupR2CacheTests(unittest.TestCase):
    def test_archive_contains_manifest_and_excludes_restore_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cache = root / "cache"
            cache.mkdir()
            (cache / "alpha_posts.json").write_text('{"entries": [{"id": "1"}]}', encoding="utf-8")
            (cache / ".r2-restored").write_text("restored\n", encoding="utf-8")
            archive = root / "cache.tar.gz"
            backup_r2_cache.create_cache_archive(cache, archive, {"alpha_posts.json"}, max_bytes=1024 * 1024)
            with tarfile.open(archive, "r:gz") as bundle:
                names = set(bundle.getnames())

            self.assertIn("cache/alpha_posts.json", names)
            self.assertIn("cache/.snapshot-manifest.json", names)
            self.assertNotIn("cache/.r2-restored", names)

    def test_size_limit_fails_before_upload(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cache = root / "cache"
            cache.mkdir()
            (cache / "alpha_posts.json").write_text('{"entries": [{"id": "1234567890"}]}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "size limit"):
                backup_r2_cache.create_cache_archive(cache, root / "cache.tar.gz", {"alpha_posts.json"}, max_bytes=1)


if __name__ == "__main__":
    unittest.main()
