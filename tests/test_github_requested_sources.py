import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))

import github


class GitHubRequestedSourcesTests(unittest.TestCase):
    def test_requested_beehiiv_feed_is_already_registered(self):
        self.assertIn(
            (
                github.STAR_HISTORY_NEWSLETTER_LABEL,
                "https://rss.beehiiv.com/feeds/BbNzf9ozGZ.xml",
                15,
            ),
            github.SOURCES,
        )

    def test_public_travnie_events_need_no_token(self):
        response = Mock()
        response.status_code = 200
        response.json.return_value = []

        with patch.object(github.requests, "get", return_value=response) as get:
            self.assertEqual(github._fetch_travnie_events(), [])

        self.assertEqual(get.call_args.args[0], github.TRAVNIE_PUBLIC_EVENTS_URL)
        self.assertNotIn("Authorization", get.call_args.kwargs["headers"])

    def test_private_event_is_not_published_even_if_returned_defensively(self):
        private_event = {
            "id": "secret-event",
            "type": "PushEvent",
            "public": False,
            "actor": {"login": "octocat"},
            "repo": {"name": "travnie/private-repo"},
            "created_at": "2026-10-04T12:00:00Z",
            "payload": {
                "ref": "refs/heads/main",
                "head": "a" * 40,
            },
        }

        with patch.object(
            github,
            "_fetch_travnie_events",
            return_value=[private_event],
        ):
            self.assertEqual(github.scrape_travnie_activity(set()), [])

    def test_push_titles_include_head_to_avoid_title_dedupe_collisions(self):
        base = {
            "type": "PushEvent",
            "public": True,
            "actor": {"login": "octocat"},
            "repo": {"name": "travnie/example"},
            "created_at": "2026-10-04T12:34:56Z",
            "payload": {"ref": "refs/heads/main"},
        }
        first = {
            **base,
            "id": "1",
            "payload": {**base["payload"], "head": "a" * 40},
        }
        second = {
            **base,
            "id": "2",
            "payload": {**base["payload"], "head": "b" * 40},
        }

        first_entry = github._normalize_travnie_event(first)
        second_entry = github._normalize_travnie_event(second)

        self.assertNotEqual(first_entry["title"], second_entry["title"])
        self.assertIn("aaaaaaa", first_entry["title"])
        self.assertIn("bbbbbbb", second_entry["title"])

    def test_comment_event_links_to_specific_comment_anchor(self):
        event = {
            "id": "comment-event",
            "type": "IssueCommentEvent",
            "public": True,
            "actor": {"login": "octocat"},
            "repo": {"name": "travnie/example"},
            "created_at": "2026-10-04T12:34:56Z",
            "payload": {
                "issue": {
                    "number": 7,
                    "html_url": "https://github.com/travnie/example/issues/7",
                },
                "comment": {
                    "id": 123,
                    "html_url": (
                        "https://github.com/travnie/example/issues/7"
                        "#issuecomment-123"
                    ),
                },
            },
        }

        entry = github._normalize_travnie_event(event)

        self.assertEqual(
            entry["link"],
            "https://github.com/travnie/example/issues/7#issuecomment-123",
        )
        self.assertIn("comment 123", entry["title"])

    def test_review_event_prefers_specific_review_url(self):
        event = {
            "id": "review-event",
            "type": "PullRequestReviewEvent",
            "public": True,
            "actor": {"login": "octocat"},
            "repo": {"name": "travnie/example"},
            "created_at": "2026-10-04T12:34:56Z",
            "payload": {
                "pull_request": {
                    "number": 11,
                    "html_url": "https://github.com/travnie/example/pull/11",
                },
                "review": {
                    "id": 789,
                    "html_url": (
                        "https://github.com/travnie/example/pull/11"
                        "#pullrequestreview-789"
                    ),
                },
            },
        }

        entry = github._normalize_travnie_event(event)

        self.assertEqual(
            entry["link"],
            "https://github.com/travnie/example/pull/11#pullrequestreview-789",
        )
        self.assertIn("review 789", entry["title"])

    def test_less_common_event_type_has_readable_action(self):
        event = {
            "id": "commit-comment-event",
            "type": "CommitCommentEvent",
            "public": True,
            "actor": {"login": "octocat"},
            "repo": {"name": "travnie/example"},
            "created_at": "2026-10-04T12:34:56Z",
            "payload": {
                "comment": {
                    "id": 321,
                    "html_url": (
                        "https://github.com/travnie/example/commit/abc"
                        "#commitcomment-321"
                    ),
                }
            },
        }

        entry = github._normalize_travnie_event(event)

        self.assertIn("commented on a commit", entry["title"])
        self.assertNotIn("commitcomment", entry["title"])

    def test_issue_comment_on_pull_request_is_labeled_as_pr(self):
        event = {
            "id": "pr-comment-event",
            "type": "IssueCommentEvent",
            "public": True,
            "actor": {"login": "octocat"},
            "repo": {"name": "travnie/example"},
            "created_at": "2026-10-04T12:34:56Z",
            "payload": {
                "issue": {
                    "number": 9,
                    "pull_request": {
                        "url": "https://api.github.com/repos/travnie/example/pulls/9"
                    },
                    "html_url": "https://github.com/travnie/example/pull/9",
                },
                "comment": {
                    "id": 456,
                    "html_url": (
                        "https://github.com/travnie/example/pull/9"
                        "#issuecomment-456"
                    ),
                },
            },
        }

        entry = github._normalize_travnie_event(event)

        self.assertIn("commented on PR #9", entry["title"])
        self.assertEqual(
            entry["link"],
            "https://github.com/travnie/example/pull/9#issuecomment-456",
        )

    def test_tag_create_event_links_to_git_tag_tree(self):
        event = {
            "id": "tag-event",
            "type": "CreateEvent",
            "public": True,
            "actor": {"login": "octocat"},
            "repo": {"name": "travnie/example"},
            "created_at": "2026-10-04T12:34:56Z",
            "payload": {"ref_type": "tag", "ref": "v1.2.3"},
        }

        entry = github._normalize_travnie_event(event)

        self.assertEqual(
            entry["link"],
            "https://github.com/travnie/example/tree/v1.2.3#feedseek-event-tag-event",
        )

    def test_github_feed_deduplicates_by_url_not_reused_titles(self):
        with patch.object(github, "run", return_value=True) as run:
            self.assertTrue(github.main())

        self.assertIsNone(run.call_args.kwargs["dedupe_title_field"])

    def test_normalizes_pull_request_event_with_unique_identity(self):
        event = {
            "id": "123456789",
            "type": "PullRequestEvent",
            "actor": {"login": "octocat"},
            "repo": {"name": "travnie/example"},
            "created_at": "2026-10-04T12:34:56Z",
            "payload": {
                "action": "opened",
                "number": 42,
                "pull_request": {
                    "html_url": "https://github.com/travnie/example/pull/42"
                },
            },
        }

        entry = github._normalize_travnie_event(event)

        self.assertEqual(
            entry["link"],
            "https://github.com/travnie/example/pull/42"
            "#feedseek-event-123456789",
        )
        self.assertEqual(
            entry["title"],
            "octocat opened PR #42 in travnie/example",
        )
        self.assertEqual(entry["source"], github.TRAVNIE_ACTIVITY_LABEL)
        self.assertEqual(
            entry["date"].isoformat(),
            "2026-10-04T12:34:56+00:00",
        )


if __name__ == "__main__":
    unittest.main()
