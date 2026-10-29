"""Source date corrections retain cached content and entry identity."""

import sys
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))

import govpl

LINK = "https://www.gov.pl/web/zdrowie/example"
OLD_DATE = datetime(2028, 8, 12, tzinfo=UTC)
CORRECT_DATE = datetime(2026, 8, 12, tzinfo=UTC)
NOW = datetime(2026, 10, 29, tzinfo=UTC)


def cached_entry(link=LINK):
    return {
        "link": link,
        "entry_id": "persisted-id",
        "title": "Published title",
        "date": OLD_DATE,
        "description": "Cached article lead",
        "image": "https://www.gov.pl/photo/example",
        "source": "Min. Zdrowia",
    }


class GovplDateTests(unittest.TestCase):
    def test_listing_corrects_known_date_without_refetching_or_replacing_metadata(self):
        entry = cached_entry()
        original = entry.copy()
        listing = '<div class="art-prev"><li>12.08.2026 <a href="/web/zdrowie/example">Edited title</a></li></div>'
        with patch.object(govpl, "fetch_text", return_value=listing), patch.object(govpl, "fetch_lead") as lead:
            new = govpl.collect_source("Min. Zdrowia", "listing", {LINK: entry})
        self.assertEqual(new, [])
        self.assertEqual(entry, {**original, "date": CORRECT_DATE})
        lead.assert_not_called()

    def test_missing_listing_date_keeps_cached_date(self):
        entry = cached_entry()
        listing = '<div class="art-prev"><li><a href="/web/zdrowie/example">Title</a></li></div>'
        with patch.object(govpl, "fetch_text", return_value=listing):
            govpl.collect_source("Min. Zdrowia", "listing", {LINK: entry})
        self.assertEqual(entry["date"], OLD_DATE)

    def test_article_recheck_repairs_an_entry_absent_from_the_current_listing(self):
        entry = cached_entry()
        original = entry.copy()
        before = govpl.generate_atom_feed([entry]).atom_str()
        with patch.object(govpl, "fetch_text", return_value='<p class="event-date">12.08.2026</p>'):
            govpl.refresh_future_dates([entry], now=NOW)
        after = govpl.generate_atom_feed([entry]).atom_str()
        self.assertEqual(entry, {**original, "date": CORRECT_DATE})
        identity = f"<id>{LINK}</id>".encode()
        self.assertIn(identity, before)
        self.assertIn(identity, after)

    def test_failed_or_unusable_rechecks_preserve_the_source_date(self):
        for page in (None, '<p>12.08.2026</p>', '<p class="event-date">31.02.2026</p>',
                     '<p class="event-date">12.08.2028</p>'):
            with self.subTest(page=page):
                entry = cached_entry()
                with patch.object(govpl, "fetch_text", return_value=page):
                    govpl.refresh_future_dates([entry], now=NOW)
                self.assertEqual(entry["date"], OLD_DATE)

    def test_rechecks_are_bounded_and_only_target_future_govpl_articles(self):
        excluded = [cached_entry("https://example.test/web/story"), cached_entry("https://www.gov.pl/other"),
                    cached_entry("https://[malformed")]
        past = {**cached_entry(), "date": CORRECT_DATE}
        future = [cached_entry(f"https://www.gov.pl/web/zdrowie/{i}") for i in range(8)]
        with patch.object(govpl, "fetch_text", return_value=None) as fetch:
            govpl.refresh_future_dates([*excluded, past, *future], now=NOW)
        self.assertEqual(fetch.call_count, govpl.MAX_DATE_RECHECKS)
        first_batch = {call.args[0] for call in fetch.call_args_list}
        self.assertTrue(first_batch <= {e["link"] for e in future})
        with patch.object(govpl, "fetch_text", return_value=None) as later:
            govpl.refresh_future_dates(future, now=NOW + timedelta(hours=8))
        self.assertEqual(first_batch | {call.args[0] for call in later.call_args_list}, {e["link"] for e in future})

    def test_one_article_failure_does_not_block_other_date_corrections(self):
        entries = [cached_entry(f"https://www.gov.pl/web/zdrowie/{i}") for i in range(2)]
        def fetch(link, **_kwargs):
            if link.endswith("/0"):
                raise RuntimeError("upstream unavailable")
            return '<p class="event-date">12.08.2026</p>'
        with patch.object(govpl, "fetch_text", side_effect=fetch):
            govpl.refresh_future_dates(entries, now=NOW)
        self.assertEqual([entry["date"] for entry in entries], [OLD_DATE, CORRECT_DATE])

    def test_main_saves_the_verified_correction_without_losing_cached_fields(self):
        entry = cached_entry()
        stored = {**entry, "date": OLD_DATE.isoformat()}
        with patch.object(govpl, "load_cache", return_value={"entries": [stored]}), \
             patch.object(govpl, "datetime") as clock, \
             patch.object(govpl, "collect_all", return_value=[]), \
             patch.object(govpl, "fetch_text", return_value='<p class="event-date">12.08.2026</p>'), \
             patch.object(govpl, "enrich_entries"), \
             patch.object(govpl, "save_cache") as save, \
             patch.object(govpl, "save_atom_feed") as publish:
            clock.now.return_value = NOW
            self.assertTrue(govpl.main())
        self.assertEqual(save.call_args.args, (govpl.FEED_NAME, [{**entry, "date": CORRECT_DATE}]))
        self.assertIn(f"<id>{LINK}</id>".encode(), publish.call_args.args[0].atom_str())


if __name__ == "__main__":
    unittest.main()
