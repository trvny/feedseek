"""Figma combined feed: native Atom sources and deduplicated Newsroom."""

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))

import figma  # noqa: E402


def parse_at_fixed_date(html, known_links):
    """Freeze time so dated Newsroom fixtures work independently of the clock."""
    with patch.object(figma, "datetime") as clock:
        clock.now.return_value = datetime(2026, 10, 28, tzinfo=timezone.utc)
        return figma.parse_newsroom(html, known_links)


class FigmaTests(unittest.TestCase):
    def test_requested_sources_and_native_blog_feed(self):
        self.assertEqual(
            figma.NEWSROOM_URL,
            "https://www.figma.com/newsroom/?lang=pl-pl",
        )
        self.assertEqual(
            {url for _, url, _ in figma.SOURCES},
            {
                "https://www.figma.com/blog/feed/atom.xml",
                "https://www.figma.com/release-notes/feed/atom.xml",
            },
        )
        self.assertEqual(figma.doc_sources(), [("Figma Newsroom", figma.NEWSROOM_URL)])

    def test_newsroom_cards_skip_duplicates_navigation_undated_and_future(self):
        html = """
        <nav><h3>Community</h3><a href="/blog/news/">News</a></nav>
        <h2>News from Figma</h2>
        <div class="cards">
          <article>
            <span>October 15, 2026</span>
            <h3>Design together with code layers</h3>
            <p>Product announcement</p>
            <a href="/blog/design-together/?lang=pl-pl&utm_source=newsroom">Learn more</a>
          </article>
          <article>
            <time datetime="2026-09-29">September 29, 2026</time>
            <h3>London office opens</h3>
            <a href="https://www.figma.com/blog/london-office/">Learn more</a>
          </article>
          <article>
            <span>September 29, 2026</span>
            <h3>London office opens</h3>
            <a href="/blog/london-office/?utm_campaign=press">Learn more</a>
          </article>
          <article><h3>Undated card</h3><a href="/blog/undated/">Learn more</a></article>
          <article>
            <span>January 1, 2099</span>
            <h3>Upcoming</h3><a href="/blog/upcoming/">Learn more</a>
          </article>
        </div>
        <h2>Media center</h2>
        <article>
          <span>October 12, 2026</span>
          <h3>Not news</h3><a href="/blog/not-news/">Learn more</a>
        </article>
        """
        posts = parse_at_fixed_date(html, set())
        self.assertEqual(
            [p["link"] for p in posts],
            ["https://figma.com/blog/design-together",
             "https://figma.com/blog/london-office"],
        )
        self.assertEqual(posts[0]["date"].strftime("%Y-%m-%d"), "2026-10-15")
        self.assertEqual(posts[0]["description"], "Product announcement")
        self.assertEqual({p["source"] for p in posts}, {"Figma Newsroom"})
        self.assertEqual(
            parse_at_fixed_date(
                html, {"https://www.figma.com/blog/design-together/?utm_medium=rss"}
            )[0]["title"],
            "London office opens",
        )

    def test_newsroom_polish_date_and_sibling_isolation(self):
        html = """
        <h2>News from Figma</h2>
        <div>
          <article><h3>Undated</h3><a href="/blog/undated/">Learn more</a></article>
          <article>
            <span>15 października 2026</span><h3>Datowany artykuł</h3>
            <a href="/blog/dated/">Learn more</a>
          </article>
        </div>
        <h2>Media center</h2>
        """
        posts = parse_at_fixed_date(html, set())
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0]["date"].strftime("%Y-%m-%d"), "2026-10-15")
        self.assertEqual(posts[0]["title"], "Datowany artykuł")

    def test_empty_or_failed_newsroom_does_not_block_native_sources(self):
        with (
            patch.object(figma.multi_rss, "get_html", return_value=None),
            patch.object(figma.multi_rss, "run", return_value=True) as run,
        ):
            self.assertEqual(figma.scrape_newsroom(set()), [])
            self.assertTrue(figma.main())

        self.assertEqual(len(run.call_args.kwargs["sources"]), 2)
        self.assertEqual(run.call_args.kwargs["extra_scrapers"], (figma.scrape_newsroom,))
        self.assertEqual(run.call_args.kwargs["source_workers"], 2)
        self.assertIsNone(run.call_args.kwargs["dedupe_title_field"])
        self.assertFalse(run.call_args.kwargs["image_backfill"])
        self.assertIs(run.call_args.kwargs["cache_transform"], figma.promote_cached_newsroom)

    def test_newsroom_cached_entry_can_be_refreshed_by_native_blog(self):
        cached = {
            "link": "https://figma.com/blog/launch",
            "title": "Early headline",
            "description": "Early summary",
            "source": "Figma Newsroom",
            "date": figma.multi_rss.parse_date("October 1, 2026"),
            "entry_id": "stable-identity",
        }
        promoted = figma.promote_cached_newsroom(cached)
        self.assertEqual(promoted["source"], "Figma Blog")
        self.assertEqual(cached["source"], "Figma Newsroom")
        self.assertEqual(promoted["entry_id"], "stable-identity")

        native = {
            "link": "https://www.figma.com/blog/launch/?utm_source=feed",
            "title": "Corrected headline",
            "description": "Corrected summary",
            "source": "Figma Blog",
            "date": figma.multi_rss.parse_date("October 2, 2026"),
        }
        with patch.object(figma.multi_rss, "scrape_feed", return_value=[native]) as scrape:
            refresh, extra = figma.multi_rss._scrape_run_native_sources(
                [("Figma Blog", figma.BLOG_FEED_URL, 80)],
                {"Figma Blog"},
                [promoted],
                {cached["link"]},
            )
        self.assertEqual(scrape.call_args.args[2], set())
        self.assertEqual(extra, [])
        merged = figma.multi_rss._merge_run_entries(
            refresh, [], [promoted], dedupe_title_field=None
        )
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["title"], "Corrected headline")
        self.assertEqual(merged[0]["description"], "Corrected summary")
        self.assertEqual(merged[0]["source"], "Figma Blog")
        self.assertEqual(merged[0]["entry_id"], "stable-identity")

    def test_newsroom_only_cache_entries_keep_their_source(self):
        entry = {
            "link": "https://figma.com/newsroom/company-update",
            "source": "Figma Newsroom",
        }
        self.assertIs(figma.promote_cached_newsroom(entry), entry)

    def test_no_newsroom_section_does_not_create_navigation_articles(self):
        self.assertEqual(
            figma.parse_newsroom(
                '<h2>Media center</h2><h3>Navigation</h3><a href="/blog/fake/">More</a>',
                set(),
            ),
            [],
        )

    def test_native_atom_and_newsroom_same_url_dedupe(self):
        existing = {
            "title": "News",
            "link": "https://www.figma.com/blog/article/?utm_source=rss",
            "date": figma.multi_rss.parse_date("October 15, 2026"),
        }
        from_newsroom = {
            "title": "News",
            "link": "https://figma.com/blog/article",
            "date": existing["date"],
        }
        posts = figma.multi_rss.dedupe_entries(
            [existing, from_newsroom],
            id_field="link",
            title_field=None,
            date_field="date",
        )
        self.assertEqual(len(posts), 1)


if __name__ == "__main__":
    unittest.main()
