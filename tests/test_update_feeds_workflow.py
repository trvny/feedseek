import unittest
from pathlib import Path


class UpdateFeedsWorkflowTests(unittest.TestCase):
    @staticmethod
    def workflow() -> str:
        return (
            Path(__file__).resolve().parents[1]
            / ".github"
            / "workflows"
            / "update-feeds.yml"
        ).read_text(encoding="utf-8")

    def test_commit_requires_final_validation_and_non_cancelled_job(self):
        workflow = self.workflow()
        block = workflow.split("- name: Commit and push successful updates", 1)[1]
        block = block.split("- name: Apply feed health gate", 1)[0]
        self.assertIn("steps.validate.outcome == 'success'", block)
        self.assertIn("!cancelled()", block)

    def test_r2_restore_is_required_before_generation(self):
        workflow = self.workflow()
        restore = workflow.split("- name: Restore Feedseek cache from R2", 1)[1]
        restore = restore.split("- name: Run feed tests", 1)[0]
        self.assertIn("tools/restore_r2_cache.py", restore)
        self.assertNotIn("continue-on-error: true", restore)
        self.assertLess(
            workflow.index("- name: Restore Feedseek cache from R2"),
            workflow.index("- name: Generate feeds"),
        )

    def test_missing_r2_snapshot_fails_closed_instead_of_full_bootstrap(self):
        workflow = self.workflow()
        restore = workflow.split("- name: Restore Feedseek cache from R2", 1)[1]
        restore = restore.split("- name: Run feed tests", 1)[0]
        generate = workflow.split("- name: Generate feeds", 1)[1]
        generate = generate.split("- name: Validate feeds", 1)[0]
        self.assertNotIn("bootstrap", restore.casefold())
        self.assertNotIn("CACHE_BOOTSTRAP", generate)
        self.assertNotIn("--full", generate)

    def test_cache_snapshot_is_saved_only_after_a_healthy_run(self):
        workflow = self.workflow()
        backup = workflow.split("- name: Back up Feedseek cache to R2", 1)[1]
        backup = backup.split("- name: Commit and push successful updates", 1)[0]
        commit = workflow.split("- name: Commit and push successful updates", 1)[1]
        commit = commit.split("- name: Apply feed health gate", 1)[0]
        self.assertIn("steps.validate.outcome == 'success'", backup)
        self.assertNotIn("bootstrap", backup.casefold())
        self.assertNotIn("continue-on-error: true", backup)
        self.assertIn("exit 1", backup)
        self.assertNotIn("git add feeds cache", commit)
        self.assertIn("git add feeds docs/sources.md", commit)
        self.assertIn("steps.backup.outcome == 'success'", commit)


if __name__ == "__main__":
    unittest.main()
