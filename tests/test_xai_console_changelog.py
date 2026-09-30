import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))

import xai


class XAIConsoleChangelogTests(unittest.TestCase):
    def test_requested_urls_are_present(self):
        self.assertEqual(xai.NEWS_URL, "https://x.ai/news")
        self.assertEqual(
            xai.CONSOLE_CHANGELOG_URL,
            "https://x.ai/api/changelog",
        )
        self.assertEqual(
            xai.BUILD_CHANGELOG_URL,
            "https://x.ai/build/changelog",
        )

    def test_parses_console_date_blocks(self):
        html = """
        <main>
          <h1>Changelog</h1>
          <p>Last updated Sep 23, 2026</p>

          <div>Sep 21, 2026</div>
          <section>
            <h2>Models</h2>
            <ul>
              <li>Grok 4.7 is available on Models</li>
              <li>Voice & Audio cards show rate limits</li>
            </ul>
          </section>

          <div>Sep 16, 2026</div>
          <section>
            <h2>Imagine, organization, and design</h2>
            <ul>
              <li>Updated the Imagine toggle in organization Preferences</li>
            </ul>
          </section>
        </main>
        """
        entries = xai._parse_console_changelog(html)

        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["title"], "Models")
        self.assertEqual(entries[0]["date"].isoformat(), "2026-09-21T00:00:00+00:00")
        self.assertEqual(entries[0]["source"], "xAI Console changelog")
        self.assertEqual(
            entries[0]["link"],
            "https://x.ai/api/changelog#console-2026-09-21-models",
        )
        self.assertIn("Grok 4.7 is available", entries[0]["description"])
        self.assertEqual(
            entries[1]["date"].isoformat(),
            "2026-09-16T00:00:00+00:00",
        )


if __name__ == "__main__":
    unittest.main()
