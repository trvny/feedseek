"""Keep cheap CI checkouts independent of generated feed history."""

import unittest
from pathlib import Path

import yaml


WORKFLOWS = Path(__file__).resolve().parents[1] / ".github" / "workflows"


class CheckoutScopeTests(unittest.TestCase):
    """Guard CI checkout boundaries and baseline comparisons."""

    @staticmethod
    def workflow(name: str) -> str:
        return (WORKFLOWS / name).read_text(encoding="utf-8")

    def test_megalinter_has_bounded_history_and_exact_comparison_baselines(self):
        workflow = self.workflow("mega-linter.yml")
        checkout = workflow.split("- name: Checkout code", 1)[1].split(
            "- name: Fetch missing comparison commits", 1
        )[0]
        self.assertIn("fetch-depth: 2", checkout)
        self.assertNotIn("fetch-depth: 0", checkout)
        self.assertIn("persist-credentials: false", checkout)
        self.assertIn('git fetch --no-tags --depth=1 origin "$sha"', workflow)
        self.assertIn('git cat-file -e "$sha^{commit}"', workflow)
        self.assertIn('git diff --quiet "$BASE_SHA" HEAD', workflow)
        self.assertNotIn("git merge-base", workflow)
        self.assertIn("github.event.pull_request.head.sha || github.sha", workflow)

    def checkout_options(self, name: str) -> dict:
        workflow = yaml.safe_load(self.workflow(name))
        checkouts = [
            step
            for job in workflow["jobs"].values()
            for step in job["steps"]
            if "actions/checkout@" in step.get("uses", "")
        ]
        self.assertEqual(len(checkouts), 1)
        return checkouts[0]["with"]

    def test_reader_ci_needs_only_site(self):
        options = self.checkout_options("reader-ci.yml")
        self.assertEqual(options["sparse-checkout"].splitlines(), ["site"])
        self.assertIs(options["persist-credentials"], False)

    def test_worker_ci_needs_only_feeds_proxy(self):
        options = self.checkout_options("worker-ci.yml")
        self.assertEqual(options["sparse-checkout"].splitlines(), ["feeds-proxy"])
        self.assertIs(options["persist-credentials"], False)


if __name__ == "__main__":
    unittest.main()
