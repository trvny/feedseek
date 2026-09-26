import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))

import xweather_log  # noqa: E402


class XweatherLogTests(unittest.TestCase):
    def test_requested_sources_are_registered(self):
        self.assertEqual(
            {url for _, url in xweather_log.SOURCES},
            {
                "https://www.xweather.com/blog",
                "https://www.xweather.com/docs/weather-api/changelog",
                "https://www.xweather.com/docs/mcp-server/changelog",
                "https://www.xweather.com/docs/android-sdk/changelog",
                "https://www.xweather.com/docs/maps-ui-sdk/changelog",
                "https://www.xweather.com/docs/webhooks/changelog",
                "https://www.xweather.com/docs/mapsgl/changelog",
                "https://www.xweather.com/docs/phrases-api/changelog",
            },
        )

    def test_parse_changelog_groups_one_entry_per_version(self):
        html = """
        <main>
          <h1>Weather API - Changelog</h1>
          <h2 id="1435">1.43.5</h2>
          <p>Sep 14, 2026</p>
          <h3>Bug Fixes</h3>
          <ul><li>Fixed the thing.</li><li>Improved another thing.</li></ul>
          <h2 id="1434">1.43.4</h2>
          <p>Aug 31, 2026</p>
          <ul><li>Added language support.</li></ul>
        </main>
        """
        entries = xweather_log.parse_changelog(
            html,
            "Weather API",
            "https://www.xweather.com/docs/weather-api/changelog",
        )
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["title"], "Weather API 1.43.5")
        self.assertEqual(entries[0]["date"].isoformat(), "2026-09-14T00:00:00+00:00")
        self.assertEqual(
            entries[0]["link"],
            "https://www.xweather.com/docs/weather-api/changelog#1435",
        )
        self.assertIn("Fixed the thing.", entries[0]["description"])
        self.assertEqual(entries[0]["category"], "Weather API")

    def test_parse_blog_uses_card_title_date_and_category(self):
        html = """
        <main>
          <article>
            <a href="/blog/category/developer">Developer</a>
            <span>Jul 14, 2026</span>
            <h3>Building with weather data: Meteorology basics for developers</h3>
            <p>Meteorology basics for developers.</p>
            <a href="/blog/building-with-weather-data">Learn more</a>
          </article>
        </main>
        """
        entries = xweather_log.parse_blog(html)
        self.assertEqual(len(entries), 1)
        self.assertEqual(
            entries[0]["title"],
            "Building with weather data: Meteorology basics for developers",
        )
        self.assertEqual(
            entries[0]["link"],
            "https://www.xweather.com/blog/building-with-weather-data",
        )
        self.assertEqual(entries[0]["date"].isoformat(), "2026-07-14T00:00:00+00:00")
        self.assertEqual(entries[0]["category"], "Developer")
        self.assertEqual(entries[0]["description"], "Meteorology basics for developers.")


if __name__ == "__main__":
    unittest.main()
