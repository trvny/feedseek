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
        self.assertEqual(tracks[0]["url"], beatport.MIRROR_SONG_BASE + UUID_TEMPLATE.format(index=1))
        self.assertEqual(tracks[0]["_mirror_week"], "2026-11-21")
        self.assertEqual(tracks[-1]["_rank"], 95)

    def test_mirror_entries_disclose_week_and_preserve_track_link(self):
        tracks = beatport.extract_mirror_tracks(mirror_html(), NOW)
        entries = beatport.build_entries(tracks, NOW)
        self.assertEqual(len(entries), 95)
        self.assertIn("Soundcharts", entries[0]["description"])
        self.assertIn("Chart week: 2026-11-21", entries[0]["description"])
        self.assertTrue(entries[0]["link"].startswith(beatport.MIRROR_SONG_BASE))
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
