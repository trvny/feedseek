import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))

from jsonfeed import build_json_feed
from safe_feed_xml import FeedXmlError, parse_feed_xml
from validate_feeds import validate_feed
import docs_sources


class SafeFeedXmlTests(unittest.TestCase):
    def test_rejects_dtds_and_entities_in_bytes_or_files(self):
        samples = (
            b'<!DOCTYPE rss SYSTEM "file:///not-a-real-file"><rss/>',
            b'<!DOCTYPE rss [<!ENTITY sample "expanded">]><rss>&sample;</rss>',
            b'<!DOCTYPE rss><rss/>',
            '<!DOCTYPE rss><rss/>'.encode("utf-16"),
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "feed_demo.xml"
            for sample in samples:
                with self.subTest(sample=sample):
                    path.write_bytes(sample)
                    for source in (sample, path):
                        with self.assertRaises(FeedXmlError):
                            parse_feed_xml(source)
                    self.assertEqual(validate_feed(path)["status"], "ERROR")
                    with patch("feedparser.parse") as parse:
                        with self.assertRaises(FeedXmlError):
                            build_json_feed(path, "demo")
                        parse.assert_not_called()
                    with patch.object(docs_sources, "FEEDS_DIR", path.parent):
                        self.assertEqual(docs_sources.feed_title("demo"), "demo")

    def test_normal_rss_and_atom_keep_metadata(self):
        for sample, title_path in (
            (b'<rss><channel><title>A &amp; B</title><!-- comment --><item/></channel></rss>', "channel/title"),
            (b'<feed xmlns="http://www.w3.org/2005/Atom"><title>A &amp; B</title><entry/></feed>',
             "{http://www.w3.org/2005/Atom}title"),
        ):
            with self.subTest(sample=sample):
                root = parse_feed_xml(sample).getroot()
                self.assertEqual(root.findtext(title_path), "A & B")

    def test_optional_comment_preservation_for_canonical_comparison(self):
        xml = b"<rss><!-- marker --><channel/></rss>"
        self.assertEqual(len(parse_feed_xml(xml).getroot()), 1)
        self.assertEqual(len(parse_feed_xml(xml, strip_ignorable=False).getroot()), 2)

    def test_malformed_xml(self):
        with self.assertRaises(FeedXmlError):
            parse_feed_xml(b"<rss>")
