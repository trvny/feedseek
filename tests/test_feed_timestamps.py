"""Channel timestamps change with published data, including entry-only updates."""

import sys
import unittest
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from feedgen.feed import FeedGenerator
from lxml import etree

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))

import utils

FIRST = datetime(2026, 10, 28, 12, tzinfo=UTC)
SECOND = datetime(2026, 10, 29, 12, tzinfo=UTC)


def feed(*, clock=FIRST, title="Example", content="Original", published=FIRST, modified=FIRST, extra=False):
    fg = FeedGenerator()
    fg.id("https://example.test/")
    fg.title(title)
    fg.description("Example feed")
    fg.link(href="https://example.test/", rel="alternate")
    fg.updated(clock)
    fg.lastBuildDate(clock)
    for number in range(2 if extra else 1):
        item = fg.add_entry()
        item.id(f"https://example.test/{number}")
        item.title(f"Entry {number}")
        item.link(href=f"https://example.test/{number}")
        item.description(content)
        item.published(published)
        item.updated(modified)
    return fg


class FeedTimestampTests(unittest.TestCase):
    def publish(self, fg, directory, format):
        writer = utils.save_atom_feed if format == "atom" else utils.save_rss_feed
        with patch.object(utils, "get_feeds_dir", return_value=directory):
            return writer(fg, "example")

    def test_unchanged_xml_and_json_keep_their_exact_published_bytes(self):
        for format in ("atom", "rss"):
            with self.subTest(format=format), TemporaryDirectory() as tmp:
                directory = Path(tmp)
                xml = self.publish(feed(), directory, format)
                original = xml.read_bytes(), xml.with_suffix(".json").read_bytes()
                self.publish(feed(clock=SECOND), directory, format)
                self.assertEqual((xml.read_bytes(), xml.with_suffix(".json").read_bytes()), original)

    def test_changed_channel_content_or_entry_dates_publish_with_the_new_clock(self):
        for format in ("atom", "rss"):
            changes = [{"title": "Renamed"}, {"content": "Edited"}, {"published": SECOND}, {"extra": True}]
            if format == "atom":
                changes.append({"modified": SECOND})
            for change in changes:
                with self.subTest(format=format, change=change), TemporaryDirectory() as tmp:
                    directory = Path(tmp)
                    xml = self.publish(feed(), directory, format)
                    before = xml.read_bytes(), xml.with_suffix(".json").read_bytes()
                    changed = feed(clock=SECOND, **change)
                    self.publish(changed, directory, format)
                    self.assertNotEqual(xml.read_bytes(), before[0])
                    self.assertNotEqual(xml.with_suffix(".json").read_bytes(), before[1])
                    self.assertEqual(changed.updated() if format == "atom" else changed.lastBuildDate(), SECOND)

    def test_removed_entry_is_a_real_change(self):
        for format in ("atom", "rss"):
            with self.subTest(format=format), TemporaryDirectory() as tmp:
                directory = Path(tmp)
                self.publish(feed(extra=True), directory, format)
                changed = feed(clock=SECOND)
                xml = self.publish(changed, directory, format)
                root = etree.fromstring(xml.read_bytes())
                entries = root.findall("{http://www.w3.org/2005/Atom}entry") if format == "atom" else root.findall("channel/item")
                self.assertEqual(len(entries), 1)
                self.assertEqual(changed.updated() if format == "atom" else changed.lastBuildDate(), SECOND)

    def test_reusing_a_generator_keeps_its_current_clock_for_later_changes(self):
        for format in ("atom", "rss"):
            with self.subTest(format=format), TemporaryDirectory() as tmp:
                directory = Path(tmp)
                xml = self.publish(feed(), directory, format)
                original = xml.read_bytes()
                reused = feed(clock=SECOND)
                self.publish(reused, directory, format)
                self.assertEqual(xml.read_bytes(), original)
                self.assertEqual(reused.updated() if format == "atom" else reused.lastBuildDate(), SECOND)
                reused.title("Later edit")
                self.publish(reused, directory, format)
                root = etree.fromstring(xml.read_bytes())
                path = "{http://www.w3.org/2005/Atom}updated" if format == "atom" else "channel/lastBuildDate"
                expected = SECOND.isoformat() if format == "atom" else "Thu, 29 Oct 2026 12:00:00 +0000"
                self.assertEqual(root.find(path).text, expected)

    def test_malformed_previous_xml_does_not_block_replacement(self):
        with TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / "feed_example.xml").write_bytes(b"<truncated")
            self.publish(feed(clock=SECOND), directory, "atom")
            self.assertEqual(etree.parse(str(directory / "feed_example.xml")).getroot().tag,
                             "{http://www.w3.org/2005/Atom}feed")

    def test_invalid_previous_date_is_repaired(self):
        for format in ("atom", "rss"):
            with self.subTest(format=format), TemporaryDirectory() as tmp:
                directory = Path(tmp)
                xml = self.publish(feed(), directory, format)
                root = etree.fromstring(xml.read_bytes())
                path = "{http://www.w3.org/2005/Atom}updated" if format == "atom" else "channel/lastBuildDate"
                root.find(path).text = "invalid"
                xml.write_bytes(etree.tostring(root, xml_declaration=True, encoding="UTF-8"))
                changed = feed(clock=SECOND)
                self.publish(changed, directory, format)
                self.assertNotIn(b">invalid<", xml.read_bytes())
                self.assertEqual(changed.updated() if format == "atom" else changed.lastBuildDate(), SECOND)


if __name__ == "__main__":
    unittest.main()
