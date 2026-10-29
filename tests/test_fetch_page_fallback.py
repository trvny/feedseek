import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))

import utils  # noqa: E402


def _response(status, text=""):
    resp = requests.Response()
    resp.status_code = status
    resp._content = text.encode()
    resp.url = "https://example.test/feed"
    return resp


class FetchPageBrowserFallbackTests(unittest.TestCase):
    def test_403_retries_with_browser_tls_when_opted_in(self):
        browser = SimpleNamespace(get=lambda url, **kw: _response(200, "<rss/>"))
        with (
            patch.object(utils.requests, "get", return_value=_response(403)),
            patch.dict(sys.modules, {"curl_cffi": SimpleNamespace(requests=browser)}),
        ):
            self.assertEqual(utils.fetch_page("https://example.test/feed", browser_fallback=True), "<rss/>")

    def test_403_raises_without_opt_in(self):
        with patch.object(utils.requests, "get", return_value=_response(403)):
            with self.assertRaises(requests.HTTPError):
                utils.fetch_page("https://example.test/feed")


if __name__ == "__main__":
    unittest.main()
