"""WebAssembly and DigitalOcean release source regressions."""

import importlib
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))

development = importlib.import_module("development")
skillsllm = importlib.import_module("skillsllm")


class RequestedSourcesTests(unittest.TestCase):
    """Source registration, JSON parsing, and failure isolation."""
    def test_webassembly_appears_once_in_development(self):
        """One WebAssembly news source in Development."""
        urls = [url for _, url, _ in development.SOURCES]
        self.assertEqual(urls.count("https://webassembly.org/feed.xml"), 1)

    def test_digitalocean_source_registry(self):
        """JSON primary plus one RSS fallback, no duplicate source."""
        urls = [url for _, url in skillsllm.doc_sources()]
        self.assertEqual(urls.count(skillsllm.DIGITALOCEAN_RELEASE_JSON_URL), 1)
        self.assertEqual(urls.count(skillsllm.DIGITALOCEAN_RELEASE_RSS_URL), 1)

    def test_json_only_accepts_dated_public_release_items(self):
        """Reject future, undated, and non-public note links."""
        raw = """
        {"title":"Recent Release Notes","items":[
          {"title":"New API tools","date":"2026-11-02",
           "url":"/release-notes/2026/11/new-api-tools/",
           "description":"<p>API tools available.</p>"},
          {"title":"Internal URL","date":"2026-11-02",
           "url":"http://localhost/secrets"},
          {"title":"Undated","url":"/release-notes/missing/"},
          {"title":"Future","date":"2099-11-02","url":"/release-notes/future/"}
        ]}
        """
        with patch.object(skillsllm, "datetime") as clock:
            clock.now.return_value = datetime(2026, 11, 8, tzinfo=timezone.utc)
            rows = skillsllm.parse_digitalocean_releases_json(raw)
        self.assertEqual(len(rows), 1)
        self.assertEqual(
            rows[0]["link"],
            "https://docs.digitalocean.com/release-notes/2026/11/new-api-tools/",
        )
        self.assertEqual(rows[0]["date"].strftime("%Y-%m-%d"), "2026-11-02")
        self.assertEqual(rows[0]["description"], "API tools available.")
        self.assertEqual(rows[0]["source"], "DigitalOcean Release Notes")

    def test_real_digitalocean_note_schema_without_title(self):
        """Derive titles from upstream note text, not invented fields."""
        raw = """
        {"notes": [
          {"date": "2026-11-05", "products": ["Droplets"],
           "text": "Droplet snapshots can now be removed from one region without deleting other copies.",
           "url": "https://docs.digitalocean.com/release-notes/november-2026/#5-november"},
          {"date": "2026-11-02", "products": ["Secrets Manager"],
           "text": "DigitalOcean Secrets Manager is now available in public preview.",
           "url": "/release-notes/november-2026/#2-november"}
        ]}
        """
        with patch.object(skillsllm, "datetime") as clock:
            clock.now.return_value = datetime(2026, 11, 8, tzinfo=timezone.utc)
            entries = skillsllm.parse_digitalocean_releases_json(raw)
        self.assertEqual(len(entries), 2)
        self.assertEqual(
            entries[0]["title"],
            "Droplet snapshots can now be removed from one region without deleting other copies.",
        )
        self.assertEqual(entries[0]["description"], entries[0]["title"])
        self.assertEqual(entries[0]["date"].strftime("%Y-%m-%d"), "2026-11-05")
        self.assertEqual(entries[1]["source"], "DigitalOcean Release Notes")

    def test_non_entry_json_falls_back_to_rss(self):
        """RSS fallback when JSON contains page metadata only."""
        rss = """
        <rss version="2.0"><channel><item>
          <title>DigitalOcean update</title>
          <link>https://docs.digitalocean.com/release-notes/november-2026/</link>
          <pubDate>Tue, 03 Nov 2026 12:00:00 GMT</pubDate>
        </item></channel></rss>
        """
        with patch.object(
            skillsllm, "fetch_url",
            side_effect=['{"title":"Recent Release Notes","body":"Page text"}', rss],
        ) as fetch:
            rows = skillsllm.collect_digitalocean_release_notes()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["source"], "DigitalOcean Release Notes")
        self.assertEqual(rows[0]["date"].strftime("%Y-%m-%d"), "2026-11-03")
        self.assertEqual(
            [call.args[0] for call in fetch.call_args_list],
            [skillsllm.DIGITALOCEAN_RELEASE_JSON_URL, skillsllm.DIGITALOCEAN_RELEASE_RSS_URL],
        )

    def test_failed_json_and_rss_are_isolated(self):
        """Both unavailable: no entries, other sources unaffected."""
        with patch.object(skillsllm, "fetch_url", side_effect=["not JSON", None]):
            self.assertEqual(skillsllm.collect_digitalocean_release_notes(), [])


if __name__ == "__main__":
    unittest.main()
