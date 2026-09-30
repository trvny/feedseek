import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))

import xai


class XAIRequestedSourcesTests(unittest.TestCase):
    def test_requested_sources_are_registered(self):
        self.assertEqual(xai.X_BLOG_URL, "https://blog.x.com/")
        self.assertEqual(
            xai.X_ENGINEERING_URL,
            "https://blog.x.com/engineering/en_us",
        )
        self.assertEqual(
            xai.GROK_RELEASE_NOTES_URL,
            "https://grok.com/release-notes",
        )

    def test_parses_x_blog_cards(self):
        html = """
        <main>
          <article>
            <span>Company</span>
            <a href="/en_us/topics/company/2024/example-post">Example X post</a>
            <p>Useful summary from the X blog.</p>
            <span>Sunday, 19 May 2024</span>
          </article>
          <a href="/en_us/tags/foo">Not an article</a>
        </main>
        """
        entries = xai._parse_x_blog_index(
            html, "X Blog", xai.X_BLOG_URL, "/en_us/topics/"
        )

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["title"], "Example X post")
        self.assertEqual(
            entries[0]["link"],
            "https://blog.x.com/en_us/topics/company/2024/example-post",
        )
        self.assertEqual(entries[0]["date"].isoformat(), "2024-05-19T00:00:00+00:00")
        self.assertEqual(entries[0]["source"], "X Blog")
        self.assertIn("Useful summary", entries[0]["description"])

    def test_parses_x_engineering_cards(self):
        html = """
        <main>
          <article>
            <a href="/engineering/en_us/topics/infrastructure/2023/blobstore">
              Twitter's Blobstore Hardware Lifecycle Monitoring and Reporting Service
            </a>
            <span>Thursday, 23 February 2023</span>
          </article>
        </main>
        """
        entries = xai._parse_x_blog_index(
            html,
            "X Engineering",
            xai.X_ENGINEERING_URL,
            "/engineering/en_us/",
        )

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["source"], "X Engineering")
        self.assertEqual(entries[0]["date"].isoformat(), "2023-02-23T00:00:00+00:00")

    def test_parses_grok_release_links_from_anchors_and_payload(self):
        html = r"""
        <main>
          <a href="/release-notes/sep-05-2026">Sep 05, 2026</a>
        </main>
        <script>
          self.__payload = {"href":"\/release-notes\/jul-25-2026"}
        </script>
        """
        entries = xai._parse_grok_release_notes_index(html)
        by_link = {entry["link"]: entry for entry in entries}

        self.assertIn("https://grok.com/release-notes/sep-05-2026", by_link)
        self.assertIn("https://grok.com/release-notes/jul-25-2026", by_link)
        self.assertEqual(
            by_link["https://grok.com/release-notes/sep-05-2026"]["date"].isoformat(),
            "2026-09-05T00:00:00+00:00",
        )
        self.assertEqual(
            by_link["https://grok.com/release-notes/sep-05-2026"]["source"],
            "Grok release notes",
        )


if __name__ == "__main__":
    unittest.main()
