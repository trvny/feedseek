import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))
import github
import github_personal as personal


def event(kind, action, payload=None, *, event_id="123", owner="trvny", actor="trvny"):
    return {
        "id": event_id, "type": kind, "public": True,
        "repo": {"name": f"{owner}/example"},
        "actor": {"login": actor, "avatar_url": "https://avatars.githubusercontent.com/u/123?v=4"},
        "created_at": "2026-11-05T09:00:00Z",
        "payload": {"action": action, **(payload or {})},
    }


class GitHubPersonalTests(unittest.TestCase):
    def test_new_pr_and_merge_are_distinct_events(self):
        pr = {
            "number": 42, "title": "Ship the feed", "merged": False,
            "html_url": "https://github.com/trvny/example/pull/42",
            "body": "Useful **release** notes",
        }
        opened = personal.normalize_event(event("PullRequestEvent", "opened",
                                                {"pull_request": pr}, event_id="1"), "User")
        merged = personal.normalize_event(event("PullRequestEvent", "closed",
                                                {"pull_request": {**pr, "merged": True}},
                                                event_id="2"), "User")
        self.assertIn("Pull request opened", opened["title"])
        self.assertIn("Pull request merged", merged["title"])
        self.assertNotEqual(opened["link"], merged["link"])
        self.assertEqual(merged["categories"], ["Pull request", "merged", "trvny/example"])
        self.assertEqual(merged["author"], "trvny")
        self.assertTrue(merged["image"].startswith("https://avatars.githubusercontent.com"))
        self.assertIn("Useful", merged["description"])

    def test_skips_pushes_closed_unmerged_prs_and_comments(self):
        pr = {"number": 1, "html_url": "https://github.com/trvny/example/pull/1",
              "merged": False}
        for kind, action, payload in [
            ("PushEvent", None, {}),
            ("PullRequestEvent", "closed", {"pull_request": pr}),
            ("IssueCommentEvent", "created", {}),
            ("PullRequestReviewEvent", "submitted", {}),
            ("CreateEvent", None, {"ref_type": "branch", "ref": "main"}),
            ("WatchEvent", "started", {}),
        ]:
            with self.subTest(kind=kind):
                self.assertIsNone(personal.normalize_event(event(kind, action, payload), "User"))

    def test_issues_releases_discussions_and_new_repository(self):
        issue = {"number": 5, "title": "Add more images",
                 "html_url": "https://github.com/travnie/example/issues/5"}
        release = {"name": "v2", "tag_name": "v2",
                   "html_url": "https://github.com/travnie/example/releases/tag/v2"}
        discussion = {"title": "Ideas",
                      "html_url": "https://github.com/travnie/example/discussions/7"}
        cases = [
            ("IssuesEvent", "opened", {"issue": issue}, "Issue"),
            ("ReleaseEvent", "published", {"release": release}, "Release"),
            ("DiscussionEvent", "created", {"discussion": discussion}, "Discussion"),
            ("CreateEvent", None, {"ref_type": "repository"}, "Repository"),
        ]
        for kind, action, payload, expected in cases:
            with self.subTest(kind=kind):
                result = personal.normalize_event(
                    event(kind, action, payload, owner="travnie", actor="other"), "Organization")
                self.assertIsNotNone(result)
                self.assertIn(expected, result["title"])

    def test_private_external_and_wrong_actor_filtered(self):
        e = event("IssuesEvent", "opened", {"issue": {"number": 7}})
        for value, stream in [
            ({**e, "public": False}, "User"),
            (event("IssuesEvent", "opened", {"issue": {"number": 1}}, owner="outside"), "User"),
            (event("IssuesEvent", "opened", {"issue": {"number": 1}}, actor="other"), "User"),
            (e, "Organization"),
        ]:
            self.assertIsNone(personal.normalize_event(value, stream))

    def test_pagination_and_tokenless_public_api(self):
        first = [event("PushEvent", None, {}, event_id=str(n)) for n in range(100)]
        reply1 = Mock(status_code=200)
        reply1.json.return_value = first
        reply2 = Mock(status_code=200)
        reply2.json.return_value = [event("IssuesEvent", "opened", {"issue": {"number": 1}})]
        with patch.object(personal.requests, "get", side_effect=[reply1, reply2]) as get:
            out = personal._fetch_events(personal.USER_EVENTS_URL)
        self.assertEqual(len(out), 101)
        self.assertEqual(get.call_count, 2)
        self.assertEqual(get.call_args_list[1].kwargs["params"]["page"], 2)
        self.assertNotIn("Authorization", get.call_args.kwargs["headers"])

    def test_dedupe_cross_stream_and_ignore_cached(self):
        e = event("IssuesEvent", "opened", {"issue": {"number": 2}})
        with patch.object(personal, "_fetch_events", side_effect=[[e], [e]]):
            found = personal.scrape_activity(set())
        self.assertEqual(len(found), 1)
        with patch.object(personal, "_fetch_events", side_effect=[[e], [e]]):
            self.assertEqual(personal.scrape_activity({found[0]["link"]}), [])

    def test_github_ecosystem_no_longer_embeds_personal_activity(self):
        self.assertNotIn("scrape_travnie_activity", {f.__name__ for f in github.EXTRA_SCRAPERS})
        self.assertFalse(github._active_cache_entry({"source": "travnie GitHub Activity"}))
        with patch.object(github, "run", return_value=True) as run:
            github.main()
        self.assertIsNone(run.call_args.kwargs["dedupe_title_field"])
        with patch.object(personal, "run", return_value=True) as run:
            personal.main()
        self.assertEqual(run.call_args.kwargs["feed_name"], "github_personal")


if __name__ == "__main__":
    unittest.main()
