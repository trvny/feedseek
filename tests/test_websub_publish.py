import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "site"))
sys.path.insert(0, str(ROOT / "tools"))

import build_site  # noqa: E402
import websub_notify  # noqa: E402

ATOM = "{http://www.w3.org/2005/Atom}"


class WebSubPublishingTests(unittest.TestCase):
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

    def test_sha_snapshot_excludes_nonpilot_feeds(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / "feed_jbzd.xml").write_text("<feed/>", encoding="utf-8")
            (directory / "feed_other.xml").write_text("<feed/>", encoding="utf-8")
            self.assertEqual(set(websub_notify.fingerprints(directory)), {"jbzd"})


if __name__ == "__main__":
    unittest.main()
