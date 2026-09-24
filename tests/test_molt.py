import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))

import molt  # noqa: E402
from molt import (  # noqa: E402
    MOLTBOOK_API_URL,
    MOLTBOOK_HOT_WINDOW,
    _fresh_unmoderated,
    _parse_date,
    doc_sources,
    fetch_moltbook_pages,
    parse_posts,
    scrape_spacemolt_changelog,
)
from utils import dedupe_entries  # noqa: E402


class MoltTests(unittest.TestCase):
    """Parser and pagination coverage for the Moltbook feed."""

    def test_moltbook_uses_bounded_hot_api(self):
        """Moltbook should be a small ranked window rather than the full new-post firehose."""
        self.assertEqual(MOLTBOOK_HOT_WINDOW, 25)
        self.assertEqual(
            MOLTBOOK_API_URL,
            "https://www.moltbook.com/api/v1/posts?sort=hot&limit=25",
        )

    def test_doc_sources_exposes_all_upstreams(self):
        """Source docs should expose both official streams and the Moltbook API."""
        self.assertEqual(
            doc_sources(),
            [
                ("SpaceMolt News", "https://spacemolt.com/news/feed.xml"),
                ("SpaceMolt Changelog", "https://spacemolt.com/changelog/rss.xml"),
                ("Moltbook Posts API", MOLTBOOK_API_URL),
            ],
        )

    def test_parse_posts_skips_spam_deleted_and_known_entries(self):
        """Only fresh, usable Moltbook posts should become feed entries."""
        payload = {
            "success": True,
            "posts": [
                {
                    "id": "good-1",
                    "title": "Agents built a tiny compiler",
                    "content": "It compiles sea shanties into bytecode.",
                    "author": {"name": "lobsterbot"},
                    "submolt": {"name": "builds", "display_name": "Builds"},
                    "score": 42,
                    "comment_count": 7,
                    "created_at": "2026-08-29T10:11:12.000Z",
                    "is_deleted": False,
                    "is_spam": False,
                },
                {
                    "id": "spam-1",
                    "title": "Buy shellcoin now",
                    "content": "spam",
                    "is_spam": True,
                },
                {
                    "id": "deleted-1",
                    "title": "Gone",
                    "content": "gone",
                    "is_deleted": True,
                },
                {
                    "id": "known-1",
                    "title": "Already cached",
                    "content": "old",
                    "submolt": {"name": "general"},
                },
            ],
        }
        known = {"https://www.moltbook.com/post/known-1"}

        entries = parse_posts(payload, known)

        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry["link"], "https://www.moltbook.com/post/good-1")
        self.assertEqual(entry["source"], "Moltbook")
        self.assertEqual(entry["submolt"], "m/builds")
        self.assertEqual(entry["date"].isoformat(), "2026-08-29T10:11:12+00:00")
        self.assertIn("m/builds", entry["description"])
        self.assertIn("lobsterbot", entry["description"])
        self.assertIn("score 42", entry["description"])
        self.assertIn("7 comments", entry["description"])

    def test_spacemolt_changelog_uses_version_fragments_as_stable_links(self):
        """Shared changelog links should not collapse distinct release entries."""
        raw_entries = [
            {
                "title": "SpaceMolt v0.607.0",
                "link": "https://spacemolt.com/changelog",
                "source": "SpaceMolt Changelog",
            },
            {
                "title": "SpaceMolt v0.606.3",
                "link": "https://spacemolt.com/changelog",
                "source": "SpaceMolt Changelog",
            },
        ]
        known = {"https://spacemolt.com/changelog#v0.606.3"}

        with patch.object(molt, "scrape_feed", return_value=raw_entries) as mocked_scrape:
            entries = scrape_spacemolt_changelog(known)

        mocked_scrape.assert_called_once_with(
            "SpaceMolt Changelog",
            "https://spacemolt.com/changelog/rss.xml",
            set(),
            cap=40,
        )
        self.assertEqual(
            [entry["link"] for entry in entries],
            ["https://spacemolt.com/changelog#v0.607.0"],
        )
        self.assertEqual(raw_entries[0]["link"], "https://spacemolt.com/changelog")

    def test_restore_submolt_migrates_legacy_cache_description(self):
        entry = {
            "source": "Moltbook",
            "description": "agent · m/research · score 7 · 2 comments",
        }

        migrated = molt._restore_submolt(entry)

        self.assertEqual(migrated["submolt"], "m/research")
        self.assertNotIn("submolt", entry)

    def test_restore_submolt_leaves_spacemolt_streams_unbucketed(self):
        entry = {
            "source": "SpaceMolt News",
            "description": "Official game news",
        }

        self.assertIs(molt._restore_submolt(entry), entry)
        self.assertNotIn("submolt", entry)

    def test_parse_date_contains_extreme_offset_overflow(self):
        """Extreme but syntactically valid offsets should degrade to no date."""
        self.assertIsNone(_parse_date("0001-01-01T00:00:00+01:00"))

    def test_parse_posts_keeps_external_link_in_description(self):
        """Link posts should still point to Moltbook while exposing their target URL."""
        payload = {
            "posts": [
                {
                    "id": "link-1",
                    "title": "Useful paper",
                    "content": "Worth reading.",
                    "url": "https://example.com/paper",
                    "author": {"name": "research-agent"},
                    "submolt": {"name": "research"},
                    "created_at": "2026-08-29T08:00:00Z",
                }
            ]
        }

        entry = parse_posts(payload, set())[0]

        self.assertEqual(entry["link"], "https://www.moltbook.com/post/link-1")
        self.assertIn("https://example.com/paper", entry["description"])

    def test_fetch_pages_follows_cursor_until_source_is_exhausted(self):
        """A burst larger than one page must be traversed through available pages."""
        pages = {
            MOLTBOOK_API_URL: {
                "success": True,
                "posts": [
                    {
                        "id": "new-1",
                        "title": "Newest",
                        "created_at": "2026-08-29T11:00:00Z",
                    },
                    {
                        "id": "known-new",
                        "title": "Newest cached",
                        "created_at": "2026-08-29T10:59:00Z",
                    },
                ],
                "has_more": True,
                "next_cursor": "page 2",
            },
            MOLTBOOK_API_URL + "&cursor=page%202": {
                "success": True,
                "posts": [
                    {
                        "id": "new-2",
                        "title": "Still new",
                        "created_at": "2026-08-29T10:58:00Z",
                    },
                    {
                        "id": "known-old",
                        "title": "Older cached",
                        "created_at": "2026-08-29T10:57:00Z",
                    },
                ],
                "has_more": False,
                "next_cursor": None,
            },
        }
        calls = []

        def fake_fetch(url, *, retry_delay):
            """Serve deterministic cursor pages to the collector."""
            self.assertEqual(retry_delay, 2)
            calls.append(url)
            return json.dumps(pages[url])

        known = {
            "https://www.moltbook.com/post/known-new",
            "https://www.moltbook.com/post/known-old",
        }
        entries, moderated, complete = fetch_moltbook_pages(known, fetch=fake_fetch)

        self.assertEqual(calls, list(pages))
        self.assertTrue(complete)
        self.assertEqual(
            [entry["link"] for entry in entries],
            [
                "https://www.moltbook.com/post/new-1",
                "https://www.moltbook.com/post/new-2",
            ],
        )
        self.assertEqual(moderated, set())

    def test_fetch_pages_trims_overflow_to_hot_window(self):
        """A partially filled first page must not let the next page overflow the hot window."""
        first_posts = [
            {"id": f"first-{index}", "title": f"First {index}"}
            for index in range(24)
        ]
        second_posts = [
            {"id": f"second-{index}", "title": f"Second {index}"}
            for index in range(25)
        ]
        pages = {
            MOLTBOOK_API_URL: {
                "success": True,
                "posts": first_posts,
                "has_more": True,
                "next_cursor": "second",
            },
            MOLTBOOK_API_URL + "&cursor=second": {
                "success": True,
                "posts": second_posts,
                "has_more": True,
                "next_cursor": "unused",
            },
        }

        def fake_fetch(url, *, retry_delay):
            """Serve enough rows to overflow the 25-post hot window."""
            self.assertEqual(retry_delay, 2)
            return json.dumps(pages[url])

        entries, moderated, complete = fetch_moltbook_pages(set(), fetch=fake_fetch)

        self.assertTrue(complete)
        self.assertEqual(moderated, set())
        self.assertEqual(len(entries), 25)
        self.assertEqual(entries[-1]["link"], "https://www.moltbook.com/post/second-0")

    def test_fetch_pages_counts_distinct_usable_posts_across_overlaps(self):
        """Overlapping cursor pages must not consume the publication-window quota twice."""
        pages = {
            MOLTBOOK_API_URL: {
                "success": True,
                "posts": [
                    {"id": "one", "title": "One"},
                    {"id": "two", "title": "Two"},
                ],
                "has_more": True,
                "next_cursor": "two",
            },
            MOLTBOOK_API_URL + "&cursor=two": {
                "success": True,
                "posts": [{"id": "two", "title": "Two"}],
                "has_more": True,
                "next_cursor": "three",
            },
            MOLTBOOK_API_URL + "&cursor=three": {
                "success": True,
                "posts": [{"id": "three", "title": "Three"}],
                "has_more": True,
                "next_cursor": "unused",
            },
        }
        calls = []

        def fake_fetch(url, *, retry_delay):
            """Serve overlapping pages and record how far pagination proceeds."""
            self.assertEqual(retry_delay, 2)
            calls.append(url)
            return json.dumps(pages[url])

        with patch.object(molt, "MOLTBOOK_HOT_WINDOW", 3):
            entries, _moderated, complete = fetch_moltbook_pages(set(), fetch=fake_fetch)

        self.assertTrue(complete)
        self.assertEqual(calls, list(pages))
        self.assertEqual(
            [entry["link"] for entry in entries],
            [
                "https://www.moltbook.com/post/one",
                "https://www.moltbook.com/post/two",
                "https://www.moltbook.com/post/three",
            ],
        )

    def test_fetch_pages_detects_moderation_below_first_cache_overlap(self):
        """The first cached hit must not hide an older post moderated later."""
        pages = {
            MOLTBOOK_API_URL: {
                "success": True,
                "posts": [
                    {"id": "known-new", "title": "Cached"},
                ],
                "has_more": True,
                "next_cursor": "older",
            },
            MOLTBOOK_API_URL + "&cursor=older": {
                "success": True,
                "posts": [
                    {
                        "id": "known-spam",
                        "title": "Now moderated",
                        "is_spam": True,
                    }
                ],
                "has_more": False,
                "next_cursor": None,
            },
        }

        def fake_fetch(url, *, retry_delay):
            """Serve one valid cached post followed by a moderated cached post."""
            self.assertEqual(retry_delay, 2)
            return json.dumps(pages[url])

        known = {
            "https://www.moltbook.com/post/known-new",
            "https://www.moltbook.com/post/known-spam",
        }
        entries, moderated, complete = fetch_moltbook_pages(known, fetch=fake_fetch)

        self.assertTrue(complete)
        self.assertEqual(entries, [])
        self.assertEqual(
            moderated, {"https://www.moltbook.com/post/known-spam"}
        )

    def test_fresh_batch_drops_post_moderated_on_overlapping_page(self):
        """A post observed as moderated later in one scan must not be published fresh."""
        link = "https://www.moltbook.com/post/flip"
        entries = [{"link": link, "title": "Initially valid"}]

        self.assertEqual(_fresh_unmoderated(entries, set(), {link}), [])

    def test_fetch_pages_rejects_empty_page_with_continuation(self):
        """An empty nonterminal page must preserve the last known-good cache."""
        pages = {
            MOLTBOOK_API_URL: {
                "success": True,
                "posts": [{"id": "new-1", "title": "Newest"}],
                "has_more": True,
                "next_cursor": "empty",
            },
            MOLTBOOK_API_URL + "&cursor=empty": {
                "success": True,
                "posts": [],
                "has_more": True,
                "next_cursor": "gap",
            },
        }

        def fake_fetch(url, *, retry_delay):
            """Serve a valid page followed by an inconsistent empty page."""
            self.assertEqual(retry_delay, 2)
            return json.dumps(pages[url])

        entries, moderated, complete = fetch_moltbook_pages(set(), fetch=fake_fetch)

        self.assertFalse(complete)
        self.assertEqual(entries, [])
        self.assertEqual(moderated, set())

    def test_fetch_pages_discards_partial_batch_after_cursor_failure(self):
        """A later page failure must not advance the cache boundary."""
        first_page = {
            "success": True,
            "posts": [
                {
                    "id": "new-1",
                    "title": "Do not persist me yet",
                    "created_at": "2026-08-29T11:00:00Z",
                }
            ],
            "has_more": True,
            "next_cursor": "broken",
        }

        def fake_fetch(url, *, retry_delay):
            """Return a good first page and fail the required cursor page."""
            self.assertEqual(retry_delay, 2)
            if url == MOLTBOOK_API_URL:
                return json.dumps(first_page)
            return None

        entries, moderated, complete = fetch_moltbook_pages(
            {"https://www.moltbook.com/post/old-boundary"}, fetch=fake_fetch
        )

        self.assertFalse(complete)
        self.assertEqual(entries, [])
        self.assertEqual(moderated, set())

    def test_parse_posts_rejects_title_removed_by_xml_sanitization(self):
        """Control-only titles must not reach feedgen as empty required fields."""
        payload = {"posts": [{"id": "bad-title", "title": "\x01\x02"}]}

        self.assertEqual(parse_posts(payload, set()), [])

    def test_fetch_pages_aborts_cursor_cycles(self):
        """Repeated cursors must fail the scrape instead of looping until timeout."""
        pages = {
            MOLTBOOK_API_URL: {
                "success": True,
                "posts": [{"id": "one", "title": "One"}],
                "has_more": True,
                "next_cursor": "loop",
            },
            MOLTBOOK_API_URL + "&cursor=loop": {
                "success": True,
                "posts": [{"id": "two", "title": "Two"}],
                "has_more": True,
                "next_cursor": "loop",
            },
        }
        calls = []

        def fake_fetch(url, *, retry_delay):
            """Serve a continuation that points back to the current cursor."""
            self.assertEqual(retry_delay, 2)
            calls.append(url)
            return json.dumps(pages[url])

        with patch.object(molt, "MOLTBOOK_HOT_WINDOW", 3):
            entries, moderated, complete = fetch_moltbook_pages(set(), fetch=fake_fetch)

        self.assertFalse(complete)
        self.assertEqual(entries, [])
        self.assertEqual(moderated, set())
        self.assertEqual(calls, list(pages))

    def test_moderated_overlap_no_longer_consumes_usable_quota(self):
        """A later spam observation must free its slot for the next valid post."""
        pages = {
            MOLTBOOK_API_URL: {
                "success": True,
                "posts": [{"id": "flip", "title": "Flip"}],
                "has_more": True,
                "next_cursor": "moderated",
            },
            MOLTBOOK_API_URL + "&cursor=moderated": {
                "success": True,
                "posts": [
                    {"id": "flip", "title": "Flip", "is_spam": True},
                    {"id": "one", "title": "One"},
                ],
                "has_more": True,
                "next_cursor": "tail",
            },
            MOLTBOOK_API_URL + "&cursor=tail": {
                "success": True,
                "posts": [{"id": "two", "title": "Two"}],
                "has_more": False,
                "next_cursor": None,
            },
        }
        calls = []

        def fake_fetch(url, *, retry_delay):
            """Flip one post to spam before two valid identities are reached."""
            self.assertEqual(retry_delay, 2)
            calls.append(url)
            return json.dumps(pages[url])

        with patch.object(molt, "MOLTBOOK_HOT_WINDOW", 2):
            entries, moderated, complete = fetch_moltbook_pages(set(), fetch=fake_fetch)

        self.assertTrue(complete)
        self.assertEqual(calls, list(pages))
        self.assertEqual(moderated, {"https://www.moltbook.com/post/flip"})
        self.assertEqual(
            [entry["link"] for entry in _fresh_unmoderated(entries, set(), moderated)],
            [
                "https://www.moltbook.com/post/one",
                "https://www.moltbook.com/post/two",
            ],
        )

    def test_identity_only_dedupe_preserves_reused_titles(self):
        """Distinct Moltbook post IDs may legitimately carry the same title."""
        entries = [
            {"link": "https://www.moltbook.com/post/one", "title": "Hello"},
            {"link": "https://www.moltbook.com/post/two", "title": "Hello"},
        ]

        self.assertEqual(len(dedupe_entries(entries, title_field=None)), 2)

    def test_main_combines_sources_with_fair_caps_and_identity_only_dedupe(self):
        """Molt should combine official streams without collapsing submolt fairness."""
        with (
            patch.object(molt, "fetch_moltbook_pages", return_value=([], set(), True)),
            patch.object(molt, "run", return_value=True) as mocked_run,
        ):
            self.assertTrue(molt.main())

        kwargs = mocked_run.call_args.kwargs
        self.assertEqual(kwargs["feed_name"], "molt")
        self.assertEqual(kwargs["title"], "Molt")
        self.assertEqual(kwargs["blog_url"], "https://www.moltbook.com/")
        self.assertEqual(kwargs["sources"], molt.SPACEMOLT_NATIVE_SOURCES)
        self.assertEqual(len(kwargs["extra_scrapers"]), 2)
        self.assertIs(kwargs["extra_scrapers"][0], molt.scrape_spacemolt_changelog)
        self.assertIsNone(kwargs["dedupe_title_field"])
        self.assertEqual(
            kwargs["per_source_cap"],
            {"": 20, "SpaceMolt News": 30, "SpaceMolt Changelog": 30},
        )
        self.assertEqual(kwargs["allocation_field"], "submolt")
        self.assertEqual(kwargs["candidate_limit"], 1000)
        self.assertEqual(
            kwargs["candidate_source_reserve"],
            {"SpaceMolt News": 30, "SpaceMolt Changelog": 30},
        )
        self.assertIs(kwargs["cache_transform"], molt._restore_submolt)

    def test_main_evicts_moltbook_posts_that_leave_hot_window(self):
        """Moltbook cache follows the current hot set without trimming SpaceMolt history."""
        hot = {
            "title": "Still hot",
            "link": "https://www.moltbook.com/post/hot-1",
            "source": "Moltbook",
            "submolt": "m/general",
        }
        with (
            patch.object(molt, "fetch_moltbook_pages", return_value=([hot], set(), True)),
            patch.object(molt, "run", return_value=True) as mocked_run,
        ):
            self.assertTrue(molt.main())

        keep_cached = mocked_run.call_args.kwargs["cache_filter"]
        self.assertTrue(keep_cached(hot))
        self.assertFalse(
            keep_cached(
                {
                    "title": "Fell out",
                    "link": "https://www.moltbook.com/post/old-hot",
                    "source": "Moltbook",
                }
            )
        )
        self.assertTrue(
            keep_cached(
                {
                    "title": "SpaceMolt release",
                    "link": "https://spacemolt.com/changelog#v1.0.0",
                    "source": "SpaceMolt Changelog",
                }
            )
        )


if __name__ == "__main__":
    unittest.main()
