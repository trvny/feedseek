import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))

import nvidia  # noqa: E402


class NvidiaTests(unittest.TestCase):
    def test_official_native_feeds_are_registered(self):
        urls = {label: url for label, url, _ in nvidia.SOURCES}
        self.assertEqual(
            urls["NVIDIA Newsroom"],
            "https://nvidianews.nvidia.com/releases.xml",
        )
        self.assertEqual(urls["NVIDIA Blog"], "https://blogs.nvidia.com/feed/")
        self.assertEqual(
            urls["NVIDIA Developer Blog"],
            "https://developer.nvidia.com/blog/feed/",
        )

    def test_geforce_news_parser_keeps_only_driver_announcements(self):
        html = """
        <main>
          <article>
            <span>July 28, 2026</span>
            <a href="/en-us/geforce/news/halo-game-ready-driver/">
              <h3>Halo: Campaign Evolved GeForce Game Ready Driver Released</h3>
            </a>
            <p>Game Ready support and optimizations.</p>
          </article>
          <article>
            <span>July 20, 2026</span>
            <a href="/en-us/geforce/news/dlss-games/">
              <h3>Five New DLSS Games This Week</h3>
            </a>
          </article>
        </main>
        """

        entries = nvidia.parse_geforce_driver_news(html)

        self.assertEqual(len(entries), 1)
        self.assertEqual(
            entries[0]["link"],
            "https://www.nvidia.com/en-us/geforce/news/halo-game-ready-driver",
        )
        self.assertEqual(entries[0]["source"], "GeForce Driver News")
        self.assertEqual(
            entries[0]["date"], datetime(2026, 7, 28, tzinfo=timezone.utc)
        )
        self.assertEqual(
            entries[0]["description"], "Game Ready support and optimizations."
        )

    def test_driver_results_parser_extracts_versions_and_fix_notes(self):
        html = """
        <div>
          Image NVIDIA Studio Driver <sup>WHQL</sup> 610.88 July 28, 2026
          Release Highlights: July Studio update.
          Fixed Application Bugs: Blender crash fixed [12345].
          Image GeForce Game Ready Driver <sup>WHQL</sup> 610.74 July 7, 2026
          Release Highlights: Game Ready for DOOM.
          Fixed General Bugs: Frame pacing improved [67890].
          Image NVIDIA Studio Driver <sup>WHQL</sup> 610.88 July 28, 2026
          Duplicate card.
        </div>
        """

        entries = nvidia.parse_geforce_driver_results(html)

        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["title"], "NVIDIA Studio Driver 610.88 WHQL")
        self.assertEqual(entries[0]["source"], "GeForce Driver Changelog")
        self.assertIn("Blender crash fixed", entries[0]["description"])
        self.assertEqual(
            entries[1]["title"], "GeForce Game Ready Driver 610.74 WHQL"
        )
        self.assertEqual(
            entries[1]["date"], datetime(2026, 7, 7, tzinfo=timezone.utc)
        )

    def test_driver_results_respect_known_links(self):
        html = (
            "GeForce Game Ready Driver WHQL 610.74 July 7, 2026 "
            "Release Highlights: Game Ready."
        )
        known = {
            nvidia.GEFORCE_DRIVER_RESULTS_URL
            + "#geforce-game-ready-610-74"
        }

        self.assertEqual(nvidia.parse_geforce_driver_results(html, known), [])


if __name__ == "__main__":
    unittest.main()
