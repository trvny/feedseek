import unittest
from pathlib import Path


class UpdateFeedsWorkflowTests(unittest.TestCase):
    def test_commit_requires_final_validation_and_non_cancelled_job(self):
        workflow = (
            Path(__file__).resolve().parents[1]
            / ".github"
            / "workflows"
            / "update-feeds.yml"
        ).read_text(encoding="utf-8")
        block = workflow.split("- name: Commit and push successful updates", 1)[1]
        block = block.split("- name: Apply feed health gate", 1)[0]

        self.assertIn("steps.validate.outcome == 'success'", block)
        self.assertIn("!cancelled()", block)

    def test_r2_is_required_before_generation(self):
        workflow = (
            Path(__file__).resolve().parents[1]
            / ".github"
            / "workflows"
            / "update-feeds.yml"
        ).read_text(encoding="utf-8")
        prepare = workflow.split("- name: Prepare R2 cache bucket", 1)[1]
        prepare = prepare.split("- name: Restore Feedseek cache from R2", 1)[0]
        restore = workflow.split("- name: Restore Feedseek cache from R2", 1)[1]
        restore = restore.split("- name: Run feed tests", 1)[0]

        self.assertNotIn("continue-on-error: true", prepare)
        self.assertNotIn("repository cache seed", prepare)
        self.assertNotIn("if: steps.r2.outputs.ready", restore)
        self.assertNotIn("repository cache seed", restore)

    def test_cache_snapshot_is_saved_only_after_a_healthy_run(self):
        workflow = (
            Path(__file__).resolve().parents[1]
            / ".github"
            / "workflows"
            / "update-feeds.yml"
        ).read_text(encoding="utf-8")
        backup = workflow.split("- name: Back up Feedseek cache to R2", 1)[1]
        backup = backup.split("- name: Commit and push successful updates", 1)[0]
        commit = workflow.split("- name: Commit and push successful updates", 1)[1]
        commit = commit.split("- name: Apply feed health gate", 1)[0]

        self.assertIn("id: backup", backup)
        self.assertNotIn("steps.generate.outcome == 'success'", backup)
        self.assertIn("steps.validate.outcome == 'success'", backup)
        self.assertNotIn("continue-on-error: true", backup)
        self.assertNotIn("keeping the existing R2 snapshot", backup)
        self.assertIn("exit 1", backup)
        self.assertNotIn("git add feeds cache", commit)
        self.assertIn("git add feeds docs/sources.md", commit)
        self.assertIn("steps.backup.outcome == 'success'", commit)


if __name__ == "__main__":
    unittest.main()
