"""Source date corrections retain cached content and entry identity."""

import sys
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from curl_cffi.requests.exceptions import Timeout as CurlTimeout

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



    def test_future_date_remains_in_cache_but_not_in_published_feed(self):
        future = {**cached_entry("https://www.gov.pl/web/premier/future"),
                  "date": datetime(2029, 6, 1, tzinfo=UTC), "source": "KPRM"}
        past = {**cached_entry("https://www.gov.pl/web/premier/published"), "date": CORRECT_DATE}
        stored = [{**e, "date": e["date"].isoformat()} for e in (future, past)]
        with patch.object(govpl, "load_cache", return_value={"entries": stored}), \
             patch.object(govpl, "datetime") as clock, \
             patch.object(govpl, "collect_all", return_value=[]), \
             patch.object(govpl, "fetch_text", return_value='<p class="event-date">01.06.2029</p>'), \
             patch.object(govpl, "enrich_entries"), \
             patch.object(govpl, "save_cache") as save, \
             patch.object(govpl, "save_atom_feed") as publish:
            clock.now.return_value = NOW
            self.assertTrue(govpl.main())
        cached = {article["link"]: article for article in save.call_args.args[1]}
        self.assertEqual(cached[future["link"]], future)
        self.assertEqual(cached[past["link"]], past)
        xml = publish.call_args.args[0].atom_str()
        self.assertIn(f"<id>{past['link']}</id>".encode(), xml)
        self.assertNotIn(f"<id>{future['link']}</id>".encode(), xml)

    def test_new_future_dated_article_is_quarantined_without_losing_other_news(self):
        future = {**cached_entry("https://www.gov.pl/web/premier/new-future"),
                  "date": datetime(2029, 6, 1, tzinfo=UTC)}
        past = {**cached_entry("https://www.gov.pl/web/premier/new-past"), "date": CORRECT_DATE}
        with patch.object(govpl, "load_cache", return_value={"entries": []}), \
             patch.object(govpl, "datetime") as clock, \
             patch.object(govpl, "collect_all", return_value=[future, past]), \
             patch.object(govpl, "enrich_entries"), \
             patch.object(govpl, "save_cache") as save, \
             patch.object(govpl, "save_atom_feed") as publish:
            clock.now.return_value = NOW
            self.assertTrue(govpl.main())
        self.assertEqual({article["link"] for article in save.call_args.args[1]},
                         {future["link"], past["link"]})
        xml = publish.call_args.args[0].atom_str()
        self.assertIn(f"<id>{past['link']}</id>".encode(), xml)
        self.assertNotIn(f"<id>{future['link']}</id>".encode(), xml)

    def test_future_only_cache_does_not_overwrite_last_good_feed(self):
        entry = cached_entry()
        with patch.object(govpl, "load_cache", return_value={
                 "entries": [{**entry, "date": OLD_DATE.isoformat()}]}), \
             patch.object(govpl, "datetime") as clock, \
             patch.object(govpl, "collect_all", return_value=[]), \
             patch.object(govpl, "fetch_text", return_value=None), \
             patch.object(govpl, "save_cache") as save, \
             patch.object(govpl, "save_atom_feed") as publish:
            clock.now.return_value = NOW
            self.assertTrue(govpl.main())
        self.assertEqual(save.call_args.args, (govpl.FEED_NAME, [entry]))
        publish.assert_not_called()


    def test_one_day_future_tolerance_does_not_hide_valid_local_dates(self):
        near = {**cached_entry(), "date": NOW + timedelta(hours=12)}
        beyond = {**cached_entry("https://www.gov.pl/web/zdrowie/too-late"),
                  "date": NOW + timedelta(days=2)}
        self.assertEqual(govpl.publishable_entries([near, beyond], now=NOW), [near])


class GovplTimeoutTests(unittest.TestCase):
    def test_two_listing_timeouts_skip_later_listings_but_keep_all_other_sources(self):
        """Host breaker affects only gov.pl listings, not native or proxy feeds."""
        circuit = govpl.GovplListingCircuit()
        rss = (
            '<rss><channel><item><title>Native entry</title><link>'
            'https://uokik.gov.pl/news</link><pubDate>Tue, 10 Nov 2026 09:00:00 GMT'
            '</pubDate></item></channel></rss>'
        )
        president = (
            '<rss><channel><item><title>President entry</title><link>'
            'https://news.google.com/rss/articles/1</link><pubDate>'
            'Tue, 10 Nov 2026 09:00:00 GMT</pubDate></item></channel></rss>'
        )
        gov_calls = []
        def fetch(url, **kwargs):
            if url.startswith("https://www.gov.pl/"):
                gov_calls.append(url)
                kwargs["on_exhausted_timeouts"]()
                return None
            return president if url.startswith("https://news.google.com/") else rss

        with patch.object(govpl, "fetch_text", side_effect=fetch), \
             patch.object(govpl, "SOURCES", [
                 ("KPRM", "https://www.gov.pl/web/premier/wydarzenia"),
                 ("MON", "https://www.gov.pl/web/obrona-narodowa/aktualnosci5"),
                 ("MSZ", "https://www.gov.pl/web/dyplomacja/aktualnosci"),
             ]), \
             patch.object(govpl, "NATIVE_RSS", [
                 ("UOKiK", "https://uokik.gov.pl/feed"),
                 ("PARP", "https://www.parp.gov.pl/?format=feed&type=rss"),
             ]):
            entries = govpl.collect_all({}, circuit=circuit)
        self.assertTrue(circuit.stalled)
        self.assertEqual(len(gov_calls), 2)
        self.assertEqual(len(entries), 3)
        self.assertEqual({e["source"] for e in entries}, {"UOKiK", "PARP", "Prezydent RP"})

    def test_typed_timeout_retry_and_non_timeout_exception(self):
        """Only timeout exceptions can notify the caller's breaker."""
        from curl_cffi import requests as creq
        response = SimpleNamespace(text="<html>OK</html>", raise_for_status=lambda: None)
        with patch.object(creq, "get", side_effect=[CurlTimeout("timeout"), response]) as get, \
             patch.object(govpl.time, "sleep"):
            signal = Mock()
            page = govpl.fetch_text("https://www.gov.pl/web/premier/wydarzenia",
                                   retries=2, on_exhausted_timeouts=signal)
        self.assertEqual(page, response.text)
        self.assertEqual(get.call_count, 2)
        signal.assert_not_called()
        with patch.object(creq, "get", side_effect=RuntimeError("timed out unrelated")) as get, \
             patch.object(govpl.time, "sleep"):
            signal = Mock()
            self.assertIsNone(govpl.fetch_text("https://www.gov.pl/web/premier/wydarzenia",
                                               retries=2, on_exhausted_timeouts=signal))
        self.assertEqual(get.call_count, 2)
        signal.assert_not_called()

    def test_article_timeout_does_not_disable_healthy_ministry_listings(self):
        """Failed article metadata requests never set the listing circuit."""
        from curl_cffi import requests as creq
        listing_1 = '<div class="art-prev"><li>10.11.2026 <a href="/web/a/item">One</a></li></div>'
        listing_2 = '<div class="art-prev"><li>10.11.2026 <a href="/web/b/item">Two</a></li></div>'
        def get(url, **_kwargs):
            if url.endswith("/listing-a"):
                return SimpleNamespace(text=listing_1, raise_for_status=lambda: None)
            if url.endswith("/listing-b"):
                return SimpleNamespace(text=listing_2, raise_for_status=lambda: None)
            raise CurlTimeout("article timeout")
        circuit = govpl.GovplListingCircuit()
        with patch.object(creq, "get", side_effect=get), \
             patch.object(govpl.time, "sleep"), \
             patch.object(govpl, "SOURCES", [("A", "https://www.gov.pl/listing-a"),
                                            ("B", "https://www.gov.pl/listing-b")]), \
             patch.object(govpl, "NATIVE_RSS", []), \
             patch.object(govpl, "collect_prezydent", return_value=[]):
            entries = govpl.collect_all({}, circuit=circuit)
        self.assertFalse(circuit.stalled)
        self.assertEqual({e["title"] for e in entries}, {"One", "Two"})

    def test_failed_refresh_keeps_cached_entry_and_avoids_host_image_backfill(self):
        """A stalled Gov.pl source must keep its saved entry unmodified."""
        entry = cached_entry()
        past = {**cached_entry("https://www.gov.pl/web/zdrowie/past"), "date": CORRECT_DATE}
        stored = [{**e, "date": e["date"].isoformat()} for e in (entry, past)]
        def stalled_collect(_cache, *, circuit):
            circuit.note_timeout()
            circuit.note_timeout()
            return []
        with patch.object(govpl, "load_cache", return_value={"entries": stored}), \
             patch.object(govpl, "collect_all", side_effect=stalled_collect), \
             patch.object(govpl, "refresh_future_dates") as dates, \
             patch.object(govpl, "enrich_entries") as enrich, \
             patch.object(govpl, "save_cache") as save, \
             patch.object(govpl, "save_atom_feed") as publish:
            self.assertTrue(govpl.main())
        dates.assert_not_called()
        enrich.assert_not_called()
        self.assertEqual({e["link"] for e in save.call_args.args[1]}, {entry["link"], past["link"]})
        xml = publish.call_args.args[0].atom_str()
        self.assertIn(f"<id>{past['link']}</id>".encode(), xml)
        self.assertNotIn(f"<id>{LINK}</id>".encode(), xml)


if __name__ == "__main__":
    unittest.main()
