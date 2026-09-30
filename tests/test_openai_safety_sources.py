import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))

import openai


class OpenAISafetySourcesTests(unittest.TestCase):
    def test_requested_sources_are_registered(self):
        rss_urls = {source[1] for source in openai.RSS_SOURCES}
        atom_urls = {source[1] for source in openai.ATOM_SOURCES}

        self.assertIn("https://alignment.openai.com/rss.xml", rss_urls)
        self.assertIn("https://status.openai.com/feed.atom", atom_urls)
        self.assertEqual(
            openai.MISALIGNMENT_REPORTS_URL,
            "https://alignment.openai.com/misalignment-reports/",
        )
        self.assertEqual(
            openai.DEPLOYMENT_SAFETY_URL,
            "https://deploymentsafety.openai.com/",
        )

    def test_parses_status_atom_entries(self):
        atom = """
        <feed xmlns="http://www.w3.org/2005/Atom">
          <entry>
            <title>Elevated errors for ChatGPT</title>
            <link href="https://status.openai.com/incidents/example" />
            <updated>2026-09-29T20:15:00Z</updated>
            <content type="html">&lt;p&gt;Monitoring a fix.&lt;/p&gt;</content>
          </entry>
        </feed>
        """
        original = openai._get_html
        try:
            openai._get_html = lambda _url: atom
            entries = openai.scrape_atom("OpenAI Status", openai.STATUS_ATOM_URL, set())
        finally:
            openai._get_html = original

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["title"], "Elevated errors for ChatGPT")
        self.assertEqual(entries[0]["link"], "https://status.openai.com/incidents/example")
        self.assertEqual(entries[0]["date"].isoformat(), "2026-09-29T20:15:00+00:00")
        self.assertIn("Monitoring a fix.", entries[0]["description"])

    def test_parses_misalignment_reports_and_notices(self):
        html = """
        <main>
          <h2>Reports</h2>
          <article>
            <h3>Self-replicating prompt injections exist</h3>
            <div>Report · Updated Sep 25, 2026 · RL self-play training</div>
            <p>We show the existence of a new variety of prompt injection.</p>
            <a href="/misalignment-reports/self-replicating-prompt-injections-exist/">
              Read full report
            </a>
          </article>
          <h2>Notices</h2>
          <article>
            <h3>RubyGems</h3>
            <div>Notice · September 11, 2026</div>
            <p>We are investigating a report about our agents' activity on RubyGems.</p>
            <a href="https://openai.com/index/rubygems-update">Read the update</a>
          </article>
        </main>
        """
        entries = openai._parse_misalignment_index(html)

        self.assertEqual(len(entries), 2)
        report, notice = entries
        self.assertEqual(
            report["link"],
            "https://alignment.openai.com/misalignment-reports/"
            "self-replicating-prompt-injections-exist/",
        )
        self.assertEqual(report["date"].isoformat(), "2026-09-25T00:00:00+00:00")
        self.assertEqual(report["source"], "OpenAI Misalignment Report")
        self.assertTrue(notice["link"].startswith(
            "https://alignment.openai.com/misalignment-reports/#notice-rubygems-"
        ))
        self.assertEqual(notice["date"].isoformat(), "2026-09-11T00:00:00+00:00")
        self.assertEqual(notice["source"], "OpenAI Misalignment Notice")

    def test_parses_deployment_safety_cards(self):
        html = """
        <main>
          <a href="/chatgpt-images-2-5">
            <span>Sep 08, 2026</span>
            <h3>ChatGPT Images 2.5 System Card</h3>
            <p>Safety evaluations and mitigations for the image models.</p>
          </a>
        </main>
        """
        entries = openai._parse_deployment_safety_index(html)

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["title"], "ChatGPT Images 2.5 System Card")
        self.assertEqual(
            entries[0]["link"],
            "https://deploymentsafety.openai.com/chatgpt-images-2-5",
        )
        self.assertEqual(entries[0]["date"].isoformat(), "2026-09-08T00:00:00+00:00")
        self.assertEqual(entries[0]["source"], "OpenAI Deployment Safety")
        self.assertIn("Safety evaluations", entries[0]["description"])


if __name__ == "__main__":
    unittest.main()
