import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "restore_published_feeds.py"
SPEC = importlib.util.spec_from_file_location("restore_published_feeds", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

BASE = "https://feeds.example/"
XML = b'<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"><title>A</title></feed>'
MODEL = json.dumps({"format": "feedseek-model-feed", "version": 1, "items": []}).encode()


def catalog(*keys):
    return {
        "format": "feedseek-model-feed-catalog",
        "version": 1,
        "feeds": [
            {"key": key, "feed_url": f"{BASE}{key}.xml", "model_feed_url": f"{BASE}{key}.json"} for key in keys
        ],
    }


class FakeResponse:
    def __init__(self, status, body):
        self.status_code = status
        self.content = body


def fake_get(files):
    def get(self, url, **kwargs):
        body = files.get(url)
        return FakeResponse(200, body) if body is not None else FakeResponse(404, b"")

    return get


class RestorePublishedFeedsTests(unittest.TestCase):
    def test_restores_every_catalog_pair_under_legacy_names(self):
        files = {
            f"{BASE}model-feeds.json": json.dumps(catalog("alpha", "beta")).encode(),
            f"{BASE}alpha.xml": XML,
            f"{BASE}alpha.json": MODEL,
            f"{BASE}beta.xml": XML,
            f"{BASE}beta.json": MODEL,
        }
        with tempfile.TemporaryDirectory() as tmp, patch.object(MODULE.requests.Session, "get", fake_get(files)):
            feeds = Path(tmp) / "feeds"
            self.assertEqual(MODULE.restore(feeds, BASE), 2)
            self.assertEqual(
                sorted(path.name for path in feeds.iterdir()),
                ["feed_alpha.json", "feed_alpha.xml", "feed_beta.json", "feed_beta.xml"],
            )

    def test_missing_pair_fails_closed_without_writing(self):
        files = {
            f"{BASE}model-feeds.json": json.dumps(catalog("alpha", "beta")).encode(),
            f"{BASE}alpha.xml": XML,
            f"{BASE}alpha.json": MODEL,
            f"{BASE}beta.xml": XML,
        }
        with tempfile.TemporaryDirectory() as tmp, patch.object(MODULE.requests.Session, "get", fake_get(files)):
            feeds = Path(tmp) / "feeds"
            with self.assertRaises(MODULE.RestoreError):
                MODULE.restore(feeds, BASE)
            self.assertFalse(feeds.exists())

    def test_invalid_xml_fails_closed(self):
        files = {
            f"{BASE}model-feeds.json": json.dumps(catalog("alpha")).encode(),
            f"{BASE}alpha.xml": b"<feed>",
            f"{BASE}alpha.json": MODEL,
        }
        with tempfile.TemporaryDirectory() as tmp, patch.object(MODULE.requests.Session, "get", fake_get(files)):
            with self.assertRaises(MODULE.RestoreError):
                MODULE.restore(Path(tmp) / "feeds", BASE)

    def test_catalog_rejects_foreign_urls_and_unsafe_keys(self):
        foreign = catalog("alpha")
        foreign["feeds"][0]["feed_url"] = "https://evil.example/alpha.xml"
        with self.assertRaises(MODULE.RestoreError):
            MODULE.catalog_entries(foreign, BASE)
        unsafe = catalog("alpha")
        unsafe["feeds"][0]["key"] = "../alpha"
        with self.assertRaises(MODULE.RestoreError):
            MODULE.catalog_entries(unsafe, BASE)


if __name__ == "__main__":
    unittest.main()
