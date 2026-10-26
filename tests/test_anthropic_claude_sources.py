"""Anthropic Alignment team and Claude developer RSS source regressions."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))

import _anthropic_base as base  # noqa: E402
import claude  # noqa: E402


class NewAnthropicClaudeSourcesTests(unittest.TestCase):
    def test_requested_sources_are_registered_once(self):
        anthology = [url for _, url, *_ in base.SOURCES]
        self.assertEqual(anthology.count("https://www.anthropic.com/research"), 1)
        self.assertEqual(anthology.count("https://www.anthropic.com/engineering"), 1)
        self.assertEqual(
            anthology.count("https://www.anthropic.com/research/team/alignment"), 1
        )
        self.assertEqual(
            [url for _, url in claude.RSS_SOURCES].count("https://claude.dev/rss.xml"), 1
        )

    def test_alignment_team_uses_nearby_date_and_ignores_team_links(self):
        html = """
        <main><table>
          <tr><td>May 7, 2026</td>
            <td><a href="/research/donating-our-open-source-alignment-tool">Study</a></td>
          </tr>
          <tr><td>May 8, 2026</td>
            <td><a href="/research/team/alignment">Alignment team</a></td>
          </tr>
        </table></main>
        """
        with (
            patch.object(base, "fetch_page", return_value=html),
            patch.object(
                base,
                "fetch_article_meta",
                return_value={"title": "Study", "summary": "Research", "image": None},
            ) as fetch_meta,
        ):
            posts = base.scrape_source(
                "Anthropic Alignment Research",
                "https://www.anthropic.com/research/team/alignment",
                "https://www.anthropic.com",
                "/research/",
                set(),
            )

        self.assertEqual(len(posts), 1)
        self.assertEqual(
            posts[0]["link"],
            "https://www.anthropic.com/research/donating-our-open-source-alignment-tool",
        )
        self.assertEqual(posts[0]["date"].strftime("%Y-%m-%d"), "2026-05-07")
        fetch_meta.assert_called_once()

    def test_overlapping_research_article_is_fetched_only_once(self):
        research = '<a href="/research/overlap">May 8, 2026 Overlap</a>'
        alignment = """
        <main>
          <div class="featured">
            <a href="/research/unique">Undated featured link</a>
          </div>
          <div><span>May 8, 2026</span><a href="/research/overlap/?utm_source=team">Overlap</a></div>
          <div><span>May 7, 2026</span><a href="/research/unique">Unique</a></div>
        </main>
        """

        def fetch(url):
            return alignment if url.endswith("/research/team/alignment") else research

        sources = [
            ("Anthropic Research", "https://www.anthropic.com/research",
             "https://www.anthropic.com", "/research/"),
            ("Anthropic Alignment Research",
             "https://www.anthropic.com/research/team/alignment",
             "https://www.anthropic.com", "/research/"),
        ]
        with (
            patch.object(base, "SOURCES", sources),
            patch.object(base, "fetch_page", side_effect=fetch),
            patch.object(
                base, "fetch_article_meta",
                return_value={"title": "Article", "summary": "", "image": None},
            ) as fetch_meta,
            patch.object(base, "scrape_red", return_value=[]),
        ):
            posts = base.scrape_all(set())

        self.assertEqual(
            [post["link"] for post in posts],
            ["https://www.anthropic.com/research/overlap",
             "https://www.anthropic.com/research/unique"],
        )
        self.assertEqual(fetch_meta.call_count, 2)
        self.assertEqual(posts[0]["source"], "Anthropic Research")
        self.assertEqual(posts[1]["source"], "Anthropic Alignment Research")

    def test_alignment_ignores_undated_link_in_shared_publication_wrapper(self):
        html = """
        <main><section>
          <a href="/research/undated">Undated report</a>
          <div><span>May 8, 2026</span>
            <a href="/research/dated">Dated report</a></div>
        </section></main>
        """
        with (
            patch.object(base, "fetch_page", return_value=html),
            patch.object(
                base, "fetch_article_meta",
                return_value={"title": "Paper", "summary": "", "image": None},
            ),
        ):
            posts = base.scrape_source(
                "Anthropic Alignment Research",
                "https://www.anthropic.com/research/team/alignment",
                "https://www.anthropic.com",
                "/research/",
                set(),
            )
        self.assertEqual(
            [post["link"] for post in posts],
            ["https://www.anthropic.com/research/dated"],
        )

    def test_new_source_empty_parses_warn_without_failing_other_sources(self):
        with (
            patch.object(base, "fetch_page", return_value="<html>Challenge</html>"),
            patch.object(base.logger, "warning") as warning,
        ):
            posts = base.scrape_source(
                "Anthropic Alignment Research",
                "https://www.anthropic.com/research/team/alignment",
                "https://www.anthropic.com",
                "/research/",
                set(),
            )
        self.assertEqual(posts, [])
        self.assertTrue(warning.called)

        with (
            patch.object(claude, "fetch_page", return_value="<rss><channel/></rss>"),
            patch.object(claude.logger, "warning") as warning,
        ):
            self.assertEqual(
                claude.scrape_rss("Claude Developer", "https://claude.dev/rss.xml", set()),
                [],
            )
        self.assertTrue(warning.called)

    def test_claude_dev_native_rss_uses_link_identity(self):
        cached = "https://claude.dev/blog/already-known"
        xml = f"""
        <rss version="2.0"><channel>
          <item>
            <title>New developer article</title>
            <link>https://claude.dev/blog/new-post</link>
            <pubDate>Thu, 15 Oct 2026 12:00:00 GMT</pubDate>
            <description>Engineering write-up</description>
          </item>
          <item><title>Cached</title><link>{cached}</link></item>
        </channel></rss>
        """
        with patch.object(claude, "fetch_page", return_value=xml):
            posts = claude.scrape_rss("Claude Developer", "https://claude.dev/rss.xml", {cached})
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0]["link"], "https://claude.dev/blog/new-post")
        self.assertEqual(posts[0]["source"], "Claude Developer")
        self.assertEqual(posts[0]["date"].strftime("%Y-%m-%d"), "2026-10-15")


if __name__ == "__main__":
    unittest.main()
