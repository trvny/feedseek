import datetime as dt
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))

import openai


class OpenAIRequestedSourcesTests(unittest.TestCase):
    def test_requested_urls_are_present_without_readding_existing_sources(self):
        rss_urls = {source[1] for source in openai.RSS_SOURCES}
        changelog_urls = {source[1] for source in openai.LI_CHANGELOGS}
        pl_urls = {source[1] for source in openai.PL_INDEX_SOURCES}

        self.assertIn("https://openai.com/products/release-notes/rss.xml", rss_urls)
        self.assertIn("https://openai.com/pl-PL/news/", pl_urls)
        self.assertIn("https://openai.com/pl-PL/research/index/", pl_urls)
        self.assertEqual(openai.DEVELOPER_BLOG_URL, "https://developers.openai.com/blog")
        self.assertEqual(
            openai.API_CHANGELOG_URL,
            "https://developers.openai.com/api/docs/changelog",
        )
        self.assertIn("https://learn.chatgpt.com/docs/changelog", changelog_urls)
        self.assertEqual(
            openai.CHATGPT_WHATS_NEW_URL,
            "https://learn.chatgpt.com/docs/whats-new",
        )

    def test_polish_index_keeps_localized_link_and_polish_date(self):
        html = """
        <main>
          <article>
            <div>Publikacja</div>
            <div>1 sie 2026</div>
            <a href="/index/ten-advances-in-mathematics/">
              <h3>Dziesięć osiągnięć w matematyce i informatyce teoretycznej</h3>
              <p>OpenAI przedstawia nowe wyniki dotyczące otwartych problemów matematyki.</p>
            </a>
          </article>
        </main>
        """
        entries = openai._parse_pl_openai_index(
            html, "OpenAI Research PL", openai.PL_RESEARCH_URL
        )

        self.assertEqual(len(entries), 1)
        self.assertEqual(
            entries[0]["link"],
            "https://openai.com/pl-PL/index/ten-advances-in-mathematics/",
        )
        self.assertEqual(entries[0]["date"].isoformat(), "2026-08-01T00:00:00+00:00")
        self.assertEqual(entries[0]["source"], "OpenAI Research PL")
        self.assertIn("OpenAI przedstawia", entries[0]["description"])

    def test_developer_blog_infers_year_across_new_year(self):
        html = """
        <main>
          <a href="/blog/new-post"><span>Jan 11</span><h3>New post</h3><p>New body.</p></a>
          <a href="/blog/old-post"><span>Dec 30</span><h3>Old post</h3><p>Old body.</p></a>
          <a href="/blog/topic/api"><span>Dec 29</span><h3>Topic page</h3></a>
        </main>
        """
        entries = openai._parse_developer_blog_index(
            html, today=dt.datetime(2026, 1, 20, tzinfo=dt.UTC)
        )

        self.assertEqual([entry["title"] for entry in entries], ["New post", "Old post"])
        self.assertEqual(entries[0]["date"].isoformat(), "2026-01-11T00:00:00+00:00")
        self.assertEqual(entries[1]["date"].isoformat(), "2025-12-30T00:00:00+00:00")
        self.assertEqual(entries[0]["source"], "OpenAI Developer Blog")

    def test_whats_new_emits_each_feature_under_week_end_date(self):
        html = """
        <main>
          <h1>What's new</h1>
          <h2>September 21–25, 2026</h2>
          <h3>Choose GPT-6 Sol and Luna</h3>
          <p>GPT-6 Sol and GPT-6 Luna are rolling out in Codex.</p>
          <h3>Another useful feature</h3>
          <p>A second weekly feature.</p>
          <h2>September 14–18, 2026</h2>
          <h3>Prepare for retirement</h3>
          <p>Plan model migrations ahead of time.</p>
        </main>
        """
        entries = openai._parse_chatgpt_whats_new(html)

        self.assertEqual(len(entries), 3)
        self.assertEqual(entries[0]["date"].isoformat(), "2026-09-25T00:00:00+00:00")
        self.assertEqual(entries[2]["date"].isoformat(), "2026-09-18T00:00:00+00:00")
        self.assertEqual(entries[0]["source"], "ChatGPT What's new")
        self.assertTrue(entries[0]["link"].startswith(
            "https://learn.chatgpt.com/docs/whats-new#whats-new-2026-09-25-"
        ))
        self.assertIn("rolling out in Codex", entries[0]["description"])


if __name__ == "__main__":
    unittest.main()
