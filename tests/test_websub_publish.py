import http.client
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from lxml import etree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "site"))
sys.path.insert(0, str(ROOT / "tools"))

import build_site  # noqa: E402
import websub_notify  # noqa: E402

ATOM = "{http://www.w3.org/2005/Atom}"


class WebSubPublishingTests(unittest.TestCase):
    """Atom/RSS discovery and notification safety contracts."""

    def test_rejects_dtd_and_external_entities_in_digest(self):
        malicious = (
            b'<!DOCTYPE feed [<!ENTITY secret SYSTEM "file:///etc/passwd">]>'
            b'<feed xmlns="http://www.w3.org/2005/Atom">'
            b'<entry><title>&secret;</title></entry></feed>'
        )
        with self.assertRaises(ValueError):
            websub_notify.entry_digest(malicious)

    def test_atom_metadata_is_idempotent_and_targets_public_topic(self):
        raw = '<feed xmlns="http://www.w3.org/2005/Atom"><title>Test</title><link rel="self" href="https://old.example/feed.xml"/></feed>'
        topic = "https://rss.bartek.lol/jbzd.xml"
        first = build_site.add_websub_links(raw, topic)
        second = build_site.add_websub_links(first, topic)
        root = ET.fromstring(second)
        links = {node.attrib["rel"]: node.attrib["href"] for node in root.findall(ATOM + "link")}
        self.assertEqual(links, {"self": topic, "hub": build_site.WEBSUB_HUB})
        self.assertEqual(first, second)

    def test_rss_contains_atom_discovery_links(self):
        raw = '<rss version="2.0"><channel><title>Test</title></channel></rss>'
        topic = "https://rss.bartek.lol/memy.xml"
        root = ET.fromstring(build_site.add_websub_links(raw, topic))
        links = root.find("channel").findall(ATOM + "link")
        self.assertEqual({node.attrib["rel"] for node in links}, {"self", "hub"})

    def test_only_changed_pilot_topics_are_published(self):
        before = {"jbzd": "a", "memy": "b", "rssboard": "c"}
        after = {"jbzd": "a", "memy": "changed", "rssboard": "c"}
        self.assertEqual(websub_notify.changed_topics(before, after), ["https://rss.bartek.lol/memy.xml"])
        with self.assertRaises(ValueError):
            websub_notify.publish(["https://evil.example/feed.xml"])

    def test_fingerprint_ignores_hub_and_channel_clock_but_detects_entry_edits(self):
        before = b'<feed xmlns="http://www.w3.org/2005/Atom"><updated>2026-01-01T00:00:00Z</updated><entry><id>a</id><title>One</title></entry></feed>'
        after = b'<feed xmlns="http://www.w3.org/2005/Atom"><updated>2026-11-21T00:00:00Z</updated><link rel="hub" href="https://pubsubhubbub.appspot.com/"/><entry><id>a</id><title>One</title></entry></feed>'
        changed = after.replace(b"<title>One</title>", b"<title>Two</title>")
        self.assertEqual(websub_notify.entry_digest(before), websub_notify.entry_digest(after))
        self.assertNotEqual(websub_notify.entry_digest(before), websub_notify.entry_digest(changed))

    def test_public_topic_verification_checks_exact_url_and_entry_digest(self):
        feed = b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>sample</id></entry></feed>'
        expected = websub_notify.entry_digest(feed)
        class PublicResponse:
            """Bounded successful public topic response."""

            status = 200

            def __init__(self):
                self.max_bytes = None

            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self, size):
                self.max_bytes = size
                return feed
        public_response = PublicResponse()
        with patch.object(
            websub_notify.urllib.request, "urlopen", return_value=public_response
        ) as fetch:
            self.assertTrue(websub_notify.public_version_ready(
                "https://rss.bartek.lol/jbzd.xml", expected
            ))
            self.assertEqual(
                fetch.call_args.args[0].full_url,
                "https://rss.bartek.lol/jbzd.xml",
            )
            self.assertEqual(public_response.max_bytes, 16 * 1024 * 1024 + 1)
        with self.assertRaises(ValueError):
            websub_notify.public_version_ready("https://evil.example/topic", expected)

    def test_truncated_public_response_does_not_block_following_topics(self):
        expected = websub_notify.entry_digest(
            b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>a</id></entry></feed>'
        )
        class TruncatedResponse:
            """Simulate a truncated upstream response."""

            status = 200
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self, size):
                raise http.client.IncompleteRead(b"partial")

        with (
            patch.object(websub_notify.urllib.request, "urlopen", return_value=TruncatedResponse()),
            patch.object(websub_notify.time, "sleep"),
        ):
            self.assertFalse(websub_notify.public_version_ready("https://rss.bartek.lol/jbzd.xml", expected))

    def test_sha_snapshot_excludes_nonpilot_feeds(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / "feed_jbzd.xml").write_text('<feed xmlns="http://www.w3.org/2005/Atom"/>', encoding="utf-8")
            (directory / "feed_other.xml").write_text("<feed/>", encoding="utf-8")
            self.assertEqual(set(websub_notify.fingerprints(directory)), {"jbzd"})


if __name__ == "__main__":
    unittest.main()
