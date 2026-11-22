"""Beatport Top 100 primary and public mirror contracts."""

import sys
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))
import beatport_top100 as beatport  # noqa: E402

NOW = datetime(2026, 11, 22, 18, 0, tzinfo=UTC)
UUID_TEMPLATE = "12345678-1234-4234-9234-{index:012x}"


def mirror_html(*, count=95, week="November 21, 2026", masked=5, gap=False):
    """Minimal Soundcharts ranking with non-public bottom rows."""
    rows = []
    for index in range(1, count + 1):
        position = index + (1 if gap and index == 10 else 0)
        url = f"/en/song/{UUID_TEMPLATE.format(index=index)}"
        rows.append(
            f'<a class="rank" href="{url}"><span class="rank__position">'
            f'{position}</span><img class="rank__image" '
            f'src="https://assets.soundcharts.com/song/{index}.jpg"/>'
            f'<span class="rank__name">Track {index}</span>'
            f'<span class="rank__artists">Artist {index}</span></a>'
        )
    for index in range(count + 1, count + masked + 1):
        rows.append(
            f'<a class="rank" href="/en/song/{UUID_TEMPLATE.format(index=index)}">'
            f'<span class="rank__position">{index}</span>'
            '<span class="rank__name">?????</span>'
            '<span class="rank__artists">????????</span></a>'
        )
    return (
        f'<html><h1>Beatport Charts - Global</h1><p>Week of {week}</p>'
        f'<div class="chart-panel__list">{"".join(rows)}</div></html>'
    )


class BeatportMirrorTests(unittest.TestCase):
    def test_public_weekly_ranking_excludes_masked_tracks(self):
        tracks = beatport.extract_mirror_tracks(mirror_html(), NOW)
        self.assertEqual(len(tracks), 95)
        self.assertEqual(tracks[0]["url"], "https://soundcharts.com/en/song/" + UUID_TEMPLATE.format(index=1))
        self.assertEqual(tracks[0]["_mirror_week"], "2026-11-21")
        self.assertEqual(tracks[-1]["_rank"], 95)

    def test_mirror_entries_disclose_week_and_preserve_track_link(self):
        tracks = beatport.extract_mirror_tracks(mirror_html(), NOW)
        entries = beatport.build_entries(tracks, NOW)
        self.assertEqual(len(entries), 95)
        self.assertIn("Soundcharts", entries[0]["description"])
        self.assertIn("Chart week: 2026-11-21", entries[0]["description"])
        self.assertTrue(entries[0]["link"].startswith("https://soundcharts.com/en/song/"))
        self.assertEqual(entries[0]["title"], "Artist 1 - Track 1")

    def test_legitimate_question_marks_do_not_mask_chart_positions(self):
        html = mirror_html().replace(
            ">Track 1</span>", ">Do You Remember?</span>"
        )
        tracks = beatport.extract_mirror_tracks(html, NOW)
        self.assertEqual(len(tracks), 95)
        self.assertEqual(tracks[0]["name"], "Do You Remember?")

    def test_rejects_stale_incomplete_and_gapped_ranking(self):
        self.assertFalse(beatport.extract_mirror_tracks(
            mirror_html(week="October 10, 2026"), NOW
        ))
        self.assertFalse(beatport.extract_mirror_tracks(mirror_html(count=12), NOW))
        self.assertFalse(beatport.extract_mirror_tracks(mirror_html(gap=True), NOW))
        self.assertFalse(beatport.extract_mirror_tracks(
            mirror_html().replace("Beatport Charts - Global", "Spotify charts"), NOW
        ))

    def test_fallback_on_primary_failure(self):
        with (
            patch.object(beatport, "fetch_chart", return_value=None),
            patch.object(beatport, "fetch_mirror_tracks",
                         return_value=beatport.extract_mirror_tracks(mirror_html(), NOW)),
            patch.object(beatport, "load_cache", return_value={"entries": []}),
            patch.object(beatport, "save_cache"),
            patch.object(beatport, "save_atom_feed") as save,
        ):
            self.assertTrue(beatport.main())
            save.assert_called_once()

    def test_cross_source_match_preserves_first_seen_and_identity(self):
        current = datetime(2026, 10, 25, 11, 0, tzinfo=UTC)
        old_link = "https://www.beatport.com/track/jamaican-bam-bam/22357262"
        old = {
            "title": "HUGEL, SOLTO (FR) - Jamaican (Bam Bam) (Extended Mix)",
            "link": old_link,
            "date": current,
            "description": "Entered Beatport Top 100 at #2",
        }
        new = {
            "title": "HUGEL & SOLTO (FR) - Jamaican (Bam Bam) [Extended Mix]",
            "link": "https://soundcharts.com/en/song/12345678-1234-4234-9234-000000000002",
            "date": NOW,
            "description": "Soundcharts mirror week",
        }
        beatport._preserve_known_links([new], [old])
        self.assertEqual(new["link"], old_link)
        merged = beatport.merge_entries([new], [old], id_field="link", date_field="date")
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["date"], current)
        self.assertEqual(merged[0]["description"], old["description"])

    def test_different_mixes_do_not_collapse(self):
        old = {
            "title": "Artist A - Anthem (Original Mix)",
            "link": "https://www.beatport.com/track/anthem/123",
        }
        new = {
            "title": "Artist A - Anthem [Extended Mix]",
            "link": "https://soundcharts.com/en/song/12345678-1234-4234-9234-000000000001",
        }
        beatport._preserve_known_links([new], [old])
        self.assertNotEqual(new["link"], old["link"])

    def test_same_provider_distinct_catalog_ids_are_not_deduplicated(self):
        old = {
            "title": "Artist A - Anthem (Extended Mix)",
            "link": "https://www.beatport.com/track/anthem/123",
            "date": NOW,
        }
        new = {
            "title": "Artist A - Anthem (Extended Mix)",
            "link": "https://www.beatport.com/track/anthem/456",
            "date": NOW,
        }
        beatport._preserve_known_links([new], [old])
        self.assertEqual(new["link"], "https://www.beatport.com/track/anthem/456")
        self.assertEqual(
            len(beatport.merge_entries([new], [old], id_field="link", date_field="date")), 2
        )

    def test_cross_source_id_remains_first_seen_link_when_direct_recovers(self):
        old = {
            "title": "Artist A - Anthem [Extended Mix]",
            "link": "https://soundcharts.com/en/song/12345678-1234-4234-9234-000000000001",
        }
        new = {
            "title": "Artist A - Anthem (Extended Mix)",
            "link": "https://www.beatport.com/track/anthem/456",
        }
        beatport._preserve_known_links([new], [old])
        self.assertEqual(new["link"], old["link"])

    def test_unusable_primary_rows_trigger_mirror(self):
        with (
            patch.object(beatport, "fetch_chart", return_value="HTML"),
            patch.object(
                beatport, "extract_tracks", return_value=[{"id": None, "name": ""}],
            ),
            patch.object(beatport, "fetch_mirror_tracks",
                         return_value=beatport.extract_mirror_tracks(mirror_html(), NOW)) as mirror,
            patch.object(beatport, "load_cache", return_value={"entries": []}),
            patch.object(beatport, "save_cache"),
            patch.object(beatport, "save_atom_feed"),
        ):
            self.assertTrue(beatport.main())
            mirror.assert_called_once()

    def test_no_mirror_means_no_writes(self):
        with (
            patch.object(beatport, "fetch_chart", return_value=None),
            patch.object(beatport, "fetch_mirror_tracks", return_value=[]),
            patch.object(beatport, "save_cache") as cache,
            patch.object(beatport, "save_atom_feed") as save,
        ):
            self.assertFalse(beatport.main())
            cache.assert_not_called()
            save.assert_not_called()


if __name__ == "__main__":
    unittest.main()
