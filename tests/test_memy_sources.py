import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))
import memy


class MemeAggregateTests(unittest.TestCase):
    def test_sources_are_distinct_and_canonical(self):
        self.assertEqual([label for label, _, _ in memy.SITES],
                         ["Memy.pl", "Jeja.pl", "Kwejk.pl"])
        samples = (
            ('<article><h2><a href="/mem/1081559/Tak_to_sie_robi?utm=1">Tak, to się robi!</a></h2>'
             '<img data-src="/uploads/mem.jpg"></article>', "Memy.pl", memy.MEMY_URL, 0),
            ('<div class="obrazek"><h2><a href="/1074059,to-uczucie.html">To uczucie</a></h2>'
             '<img src="https://v4.jeja.pl/a.jpg"></div>', "Jeja.pl", memy.JEJA_URL, 1),
            ('<article><h2><a href="/obrazek/4209647/ogromna-kijanka.html">Ogromna kijanka</a></h2>'
             '<img src="https://i1.kwejk.pl/1.jpg"></article>', "Kwejk.pl", memy.KWEJK_URL, 2),
        )
        for html, label, base, index in samples:
            with self.subTest(label=label):
                found = memy.parse_listing(html, label, base, memy.SITES[index][2], set())
                self.assertEqual(len(found), 1)
                self.assertEqual(found[0]["source"], label)
                expected_images = (
                    "https://memy.pl/uploads/mem.jpg",
                    "https://v4.jeja.pl/a.jpg",
                    "https://i1.kwejk.pl/1.jpg",
                )
                expected_links = (
                    "https://memy.pl/mem/1081559/Tak_to_sie_robi",
                    "https://memy.jeja.pl/1074059,to-uczucie.html",
                    "https://kwejk.pl/obrazek/4209647/ogromna-kijanka.html",
                )
                self.assertEqual(found[0]["image"], expected_images[index])
                self.assertEqual(found[0]["link"], expected_links[index])
                self.assertIsNone(found[0]["date"])

    def test_skips_cached_and_untrusted_links(self):
        html = ('<article><a href="/mem/123/foo">Foo</a><img src="https://memy.pl/a.jpg"></article>'
                '<article><a href="https://other.example/mem/124/bar">Bar</a></article>')
        result = memy.parse_listing(html, "Memy.pl", memy.MEMY_URL,
                                    memy.SITES[0][2], {"https://memy.pl/mem/123/foo"})
        self.assertEqual(result, [])

    def test_partial_failure_does_not_block_other_sources(self):
        html = '<article><h2><a href="/obrazek/12/funny.html">Funny</a></h2></article>'
        with patch.object(memy, "get_html", side_effect=[None, None, html]):
            found = memy.scrape_meme_sites(set())
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["source"], "Kwejk.pl")

    def test_video_poster_not_mp4_thumbnail(self):
        from bs4 import BeautifulSoup
        card = BeautifulSoup('<article><video src="https://x.test/video.mp4" '
                             'poster="https://x.test/preview.jpg"></video></article>',
                             "html.parser").article
        self.assertEqual(memy._image(card, memy.MEMY_URL), "https://x.test/preview.jpg")

    def test_malformed_url_does_not_poison_other_items(self):
        html = ('<article><a href="https://[invalid/mem/1/a">Bad</a></article>'
                '<article><h2><a href="/mem/123/good">Good</a></h2></article>')
        self.assertEqual(len(memy.parse_listing(html, "Memy.pl", memy.MEMY_URL,
                                                memy.SITES[0][2], set())), 1)

    def test_first_seen_is_updated_not_fake_published(self):
        from multi_rss import generate_atom_feed
        with patch.object(memy, "get_html", side_effect=[
            '<article><h2><a href="/mem/1/new">New</a></h2></article>', None, None,
        ]):
            items = memy.scrape_meme_sites(set())
        self.assertEqual(items[0]["date_kind"], "first_seen")
        self.assertIsNotNone(items[0]["date"])
        xml = generate_atom_feed(items, feed_name="memy", feed_id=memy.MEMY_URL,
                                 title="Memy", subtitle="Memy", blog_url=memy.MEMY_URL,
                                 author="Memy").atom_str().decode()
        self.assertIn("<updated>", xml)
        self.assertNotIn("<published>", xml)
        self.assertIn("first-seen", xml)

    def test_pipeline_exports_atom_and_mrss_images(self):
        with patch.object(memy, "run", return_value=True) as run:
            self.assertTrue(memy.main())
        self.assertEqual(run.call_args.kwargs["feed_name"], "memy")
        self.assertEqual(run.call_args.kwargs["dedupe_title_field"], None)
        self.assertEqual(run.call_args.kwargs["language"], "pl")


if __name__ == "__main__":
    unittest.main()
