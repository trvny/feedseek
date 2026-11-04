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
          <a href="introducing-agentid"><h2>Introducing AgentID</h2></a>
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
            entries = skillsllm.collect_agentid_blog(set(), skillsllm.AttemptLedger())
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["title"], "Introducing AgentID")
        self.assertEqual(entries[0]["source"], "AgentID Blog")
        self.assertEqual(entries[0]["category"], "agentid")
        self.assertEqual(
            entries[0]["date"].isoformat(), "2026-10-06T10:00:00+00:00"
        )
        self.assertEqual(entries[0]["description"], "Agent sign-in with OIDC")

    def test_agentid_broken_page_stops_after_retry_budget(self):
        index = '<a href="broken-post">Broken</a>'
        link = "https://www.agentid.com/blog/broken-post"
        ledger = skillsllm.AttemptLedger()
        with patch.object(skillsllm, "fetch_url", return_value=index):
            with patch.object(skillsllm, "fetch_detail", return_value=None) as detail:
                self.assertEqual(skillsllm.collect_agentid_blog(set(), ledger), [])
                detail.assert_called_once()

        for count in range(1, skillsllm.MAX_FETCH_ATTEMPTS):
            ledger = skillsllm.AttemptLedger(ledger.current)
            with patch.object(skillsllm, "fetch_url", return_value=index):
                with patch.object(skillsllm, "fetch_detail", return_value=None) as detail:
                    self.assertEqual(skillsllm.collect_agentid_blog(set(), ledger), [])
                    detail.assert_called_once()

        exhausted = skillsllm.AttemptLedger(ledger.current)
        with patch.object(skillsllm, "fetch_url", return_value=index):
            with patch.object(skillsllm, "fetch_detail") as detail:
                self.assertEqual(skillsllm.collect_agentid_blog(set(), exhausted), [])
                detail.assert_not_called()
        self.assertEqual(exhausted.skipped, 1)
        self.assertEqual(exhausted.current["AgentID Blog"][link], skillsllm.MAX_FETCH_ATTEMPTS)

    def test_agentid_cached_links_do_not_consume_new_post_budget(self):
        old = {f"https://www.agentid.com/blog/old-{n}" for n in range(25)}
        anchors = "".join(
            f'<a href="/blog/old-{n}">Old</a>' for n in range(25)
        )
        anchors += '<a href="/blog/new-post">New</a>'
        post = "<html><head><title>New AgentID Post</title></head></html>"

        def fake_fetch(url):
            if url == skillsllm.AGENTID_BLOG_URL:
                return anchors
            if url == "https://www.agentid.com/blog/new-post":
                return post
            raise AssertionError(f"unexpected fetch: {url}")

        with patch.object(skillsllm, "fetch_url", side_effect=fake_fetch):
            entries = skillsllm.collect_agentid_blog(old, skillsllm.AttemptLedger())
        self.assertEqual([item["title"] for item in entries], ["New AgentID Post"])

    def test_agentid_exhausted_urls_do_not_starve_new_posts(self):
        old = [f"https://www.agentid.com/blog/dead-{n}" for n in range(25)]
        index = "".join(f'<a href="/blog/dead-{n}">Dead</a>' for n in range(25))
        index += '<a href="/blog/new-post">New</a>'
        previous = {"AgentID Blog": {url: skillsllm.MAX_FETCH_ATTEMPTS for url in old}}
        ledger = skillsllm.AttemptLedger(previous)
        detail = "<html><head><title>Fresh AgentID Article</title></head></html>"

        with patch.object(skillsllm, "fetch_url", return_value=index):
            with patch.object(skillsllm, "fetch_detail", return_value={
                "title": "Fresh AgentID Article",
                "link": "https://www.agentid.com/blog/new-post",
                "date": skillsllm.stable_fallback_date("https://www.agentid.com/blog/new-post"),
                "description": "Fresh AgentID Article",
                "source": "AgentID Blog",
                "category": "agentid",
                "image": None,
            }) as fetch:
                entries = skillsllm.collect_agentid_blog(set(), ledger)
                fetch.assert_called_once()
        self.assertEqual([entry["title"] for entry in entries], ["Fresh AgentID Article"])
        self.assertEqual(ledger.skipped, 25)

    def test_agentid_index_outage_keeps_failure_ledger(self):
        url = "https://www.agentid.com/blog/broken-post"
        ledger = skillsllm.AttemptLedger({"AgentID Blog": {url: 2}})
        with patch.object(skillsllm, "fetch_url", return_value=None):
            self.assertEqual(skillsllm.collect_agentid_blog(set(), ledger), [])
        self.assertEqual(ledger.current["AgentID Blog"][url], 2)

    def test_agentid_unavailable_index_returns_no_entries(self):
        with patch.object(skillsllm, "fetch_url", return_value=None):
            self.assertEqual(skillsllm.collect_agentid_blog(set(), skillsllm.AttemptLedger()), [])


if __name__ == "__main__":
    unittest.main()
