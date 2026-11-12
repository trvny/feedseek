import sys
import tarfile
import tempfile
import unittest
from subprocess import CompletedProcess
from unittest import mock
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

    def test_intentionally_empty_cache_is_valid_durable_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cache = root / "cache"
            cache.mkdir()
            (cache / "saas_posts.json").write_text(
                '{"entries": [], "intentional_empty": true}', encoding="utf-8"
            )
            archive = root / "cache.tar.gz"
            backup_r2_cache.create_cache_archive(
                cache, archive, {"saas_posts.json"}, max_bytes=1024 * 1024
            )
            with tarfile.open(archive, "r:gz") as bundle:
                self.assertIn("cache/saas_posts.json", bundle.getnames())

    def test_retry_classifier_is_limited_to_explicit_transient_http_errors(self):
        """Match all supported gateway statuses, not arbitrary error text."""
        responses = {
            429: "Too Many Requests",
            500: "Internal Server Error",
            502: "Bad Gateway",
            503: "Service Unavailable",
            504: "Gateway Timeout",
            520: "Web server is returning an unknown error",
            521: "Web server is down",
            522: "Connection timed out",
            523: "Origin is unreachable",
            524: "A timeout occurred",
        }
        for status, description in responses.items():
            with self.subTest(status=status):
                self.assertTrue(backup_r2_cache.is_retryable_upload_error(
                    f"Failed to fetch /accounts/redacted - {status}: {description};"
                ))
                self.assertTrue(backup_r2_cache.is_retryable_upload_error(
                    f"Error code {status}"
                ))
                self.assertTrue(backup_r2_cache.is_retryable_upload_error(
                    f"{status} {description}"
                ))
                self.assertTrue(backup_r2_cache.is_retryable_upload_error(
                    f"HTTP {status}"
                ))
        for message in ("401: Unauthorized", "403: Forbidden", "NoSuchKey", "Error code 5021"):
            with self.subTest(message=message):
                self.assertFalse(backup_r2_cache.is_retryable_upload_error(message))

    def test_gateway_failure_retries_same_archive(self):
        """Transient Cloudflare 502 must not lose a valid cache snapshot."""
        failed = CompletedProcess([], 1, "", "Failed to fetch /accounts/redacted/r2/... - 502: Bad Gateway;")
        success = CompletedProcess([], 0, "Uploaded", "")
        with mock.patch.dict(backup_r2_cache.os.environ, {
            "CLOUDFLARE_API_TOKEN": str(id(self)),
            "CLOUDFLARE_ACCOUNT_ID": "test",
        }), mock.patch.object(backup_r2_cache, "_wrangler_path", return_value=Path("wrangler")), \
             mock.patch.object(backup_r2_cache.subprocess, "run", side_effect=[failed, success]) as run, \
             mock.patch.object(backup_r2_cache.time, "sleep") as sleep:
            backup_r2_cache.upload_archive("feedseek-cache", "snapshots/cache.tar.gz", Path("cache.tar.gz"))
        self.assertEqual(run.call_count, 2)
        self.assertEqual(run.call_args_list[0].args[0], run.call_args_list[1].args[0])
        for upload in run.call_args_list:
            args = upload.args[0]
            self.assertEqual(args[args.index("--file") + 1], "cache.tar.gz")
            self.assertIn("feedseek-cache/snapshots/cache.tar.gz", args)
        sleep.assert_called_once_with(5)

    def test_non_transient_error_fails_without_retry(self):
        """Authentication failures must not be hidden by retries."""
        failed = CompletedProcess([], 1, "", "Failed to fetch /accounts/redacted/r2/... - 403: Forbidden;")
        with mock.patch.dict(backup_r2_cache.os.environ, {
            "CLOUDFLARE_API_TOKEN": str(id(self)),
            "CLOUDFLARE_ACCOUNT_ID": "test",
        }), mock.patch.object(backup_r2_cache, "_wrangler_path", return_value=Path("wrangler")), \
             mock.patch.object(backup_r2_cache.subprocess, "run", return_value=failed) as run, \
             mock.patch.object(backup_r2_cache.time, "sleep") as sleep:
            with self.assertRaisesRegex(RuntimeError, "403: Forbidden"):
                backup_r2_cache.upload_archive("feedseek-cache", "snapshots/cache.tar.gz", Path("cache.tar.gz"))
        run.assert_called_once()
        sleep.assert_not_called()

    def test_repeated_gateway_errors_exhaust_retry_budget(self):
        """Persistent R2 errors fail closed and block publication."""
        failed = CompletedProcess([], 1, "", "Error code 502")
        with mock.patch.dict(backup_r2_cache.os.environ, {
            "CLOUDFLARE_API_TOKEN": str(id(self)),
            "CLOUDFLARE_ACCOUNT_ID": "test",
        }), mock.patch.object(backup_r2_cache, "_wrangler_path", return_value=Path("wrangler")), \
             mock.patch.object(backup_r2_cache.subprocess, "run", return_value=failed) as run, \
             mock.patch.object(backup_r2_cache.time, "sleep") as sleep:
            with self.assertRaisesRegex(RuntimeError, "502"):
                backup_r2_cache.upload_archive("feedseek-cache", "snapshots/cache.tar.gz", Path("cache.tar.gz"))
        self.assertEqual(run.call_count, backup_r2_cache.MAX_UPLOAD_ATTEMPTS)
        self.assertEqual(sleep.call_count, backup_r2_cache.MAX_UPLOAD_ATTEMPTS - 1)

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
