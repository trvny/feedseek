"""AgentMail/AgentID additions to the SkillsLLM aggregate."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))

import skillsllm  # noqa: E402


class AgentIdentitySourcesTests(unittest.TestCase):
    def test_agentmail_native_feed_and_agentid_docs(self):
        native = {row[0]: row[1] for row in skillsllm.NATIVE_FEEDS}
        self.assertEqual(
            native["AgentMail Changelog"], "https://docs.agentmail.to/changelog.rss"
        )
        self.assertEqual(
            dict(skillsllm.doc_sources())["AgentID Blog"],
            "https://www.agentid.com/blog",
        )

    def test_agentid_links_filter_categories_duplicates_and_known_posts(self):
        html = """
        <main>
          <a href="/blog">All posts</a>
          <a href="/blog/introducing-agentid"><h2>Introducing AgentID</h2></a>
          <a href="/blog/introducing-agentid?ref=home">Repeated post</a>
          <a href="https://www.agentid.com/blog/agentid-for-descope#details">Descope</a>
          <a href="/blog/category/identity">Filter</a>
          <a href="https://other.example/blog/foreign">Foreign</a>
        </main>
        """
        links = skillsllm.agentid_article_links(
            html, {"https://www.agentid.com/blog/agentid-for-descope"}
        )
        self.assertEqual(
            links, ["https://www.agentid.com/blog/introducing-agentid"]
        )

    def test_agentid_collect_isolated_and_preserves_published_date(self):
        index = (
            '<a href="/blog/introducing-agentid">Intro</a>'
            '<a href="/blog/broken-post">Broken</a>'
        )
        detail = """
        <html><head>
          <title>Introducing AgentID | AgentID</title>
          <meta name="description" content="Agent sign-in with OIDC">
          <meta property="article:published_time" content="2026-10-06T10:00:00Z">
        </head></html>
        """
        pages = {
            skillsllm.AGENTID_BLOG_URL: index,
            "https://www.agentid.com/blog/introducing-agentid": detail,
        }
        with patch.object(skillsllm, "fetch_url", side_effect=pages.get):
            entries = skillsllm.collect_agentid_blog(set())
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["title"], "Introducing AgentID")
        self.assertEqual(entries[0]["source"], "AgentID Blog")
        self.assertEqual(entries[0]["category"], "agentid")
        self.assertEqual(
            entries[0]["date"].isoformat(), "2026-10-06T10:00:00+00:00"
        )
        self.assertEqual(entries[0]["description"], "Agent sign-in with OIDC")

    def test_agentid_unavailable_index_returns_no_entries(self):
        with patch.object(skillsllm, "fetch_url", return_value=None):
            self.assertEqual(skillsllm.collect_agentid_blog(set()), [])


if __name__ == "__main__":
    unittest.main()
