"""Blocked and rate-limited URLs never count as verified source access."""

import io
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import check_sources  # noqa: E402

URL = "https://source.example.test/feed"


class SourceProbeTests(unittest.TestCase):
    def probe(self, primary, fallback):
        response = Mock(status_code=primary)
        with (
            patch.object(check_sources.requests, "get", return_value=response),
            patch.object(check_sources, "_impersonated_status", return_value=fallback),
        ):
            result = check_sources.probe(URL)
        response.close.assert_called_once()
        return result

    def test_a_successful_fallback_verifies_source_access(self):
        self.assertEqual(self.probe(403, 200), (True, "200 (curl_cffi fallback)"))

    def test_rejected_access_is_not_reported_healthy(self):
        for status, reason in ((401, "authentication required"), (403, "access blocked"), (429, "rate limited")):
            with self.subTest(status=status):
                ok, note = self.probe(status, status)
                self.assertFalse(ok)
                self.assertIn(reason, note)
                self.assertIn("source not verified", note)

    def test_failed_fallback_uses_primary_status_when_unavailable(self):
        ok, note = self.probe(403, None)
        self.assertFalse(ok)
        self.assertIn("HTTP 403", note)

    def test_a_later_server_error_does_not_inherit_an_earlier_block_as_success(self):
        self.assertEqual(self.probe(403, 503), (False, "HTTP 503"))

    def test_connection_failures_remain_failures(self):
        with (
            patch.object(check_sources.requests, "get", side_effect=check_sources.requests.ConnectionError()),
            patch.object(check_sources, "_impersonated_status", return_value=None),
        ):
            self.assertEqual(check_sources.probe(URL), (False, "ConnectionError"))

    def test_cli_fails_when_source_access_remains_unverified(self):
        with (
            patch.object(sys, "argv", ["check_sources.py", "--broken"]),
            patch.object(check_sources, "load_yaml_feeds", return_value={"demo": {}}),
            patch.object(check_sources, "collect_sources", return_value=([("Source", URL)], "generator")),
            patch.object(
                check_sources, "probe", return_value=(False, "HTTP 403 (access blocked; source not verified)")
            ),
            patch("sys.stdout", new_callable=io.StringIO) as output,
        ):
            self.assertEqual(check_sources.main(), 1)
        self.assertIn("1 of 1 sources need attention", output.getvalue())


if __name__ == "__main__":
    unittest.main()
