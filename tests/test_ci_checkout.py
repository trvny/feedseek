"""Keep cheap CI checkouts independent of generated feed history."""

import unittest
from pathlib import Path


WORKFLOWS = Path(__file__).resolve().parents[1] / ".github" / "workflows"


class CheckoutScopeTests(unittest.TestCase):
    def workflow(self, name: str) -> str:
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

    def test_reader_ci_needs_only_site(self):
        workflow = self.workflow("reader-ci.yml")
        self.assertIn("sparse-checkout: |\n            site", workflow)
        self.assertIn("persist-credentials: false", workflow)

    def test_worker_ci_needs_only_feeds_proxy(self):
        workflow = self.workflow("worker-ci.yml")
        self.assertIn("sparse-checkout: |\n            feeds-proxy", workflow)
        self.assertIn("persist-credentials: false", workflow)


if __name__ == "__main__":
    unittest.main()
