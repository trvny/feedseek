import unittest
from pathlib import Path


class UpdateFeedsWorkflowTests(unittest.TestCase):
    @staticmethod
    def workflow() -> str:
        return (Path(__file__).resolve().parents[1] / ".github" / "workflows" / "update-feeds.yml").read_text(
            encoding="utf-8"
        )

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
        self.assertIn("tools/backup_r2_cache.py", backup)
        self.assertNotIn("wrangler r2 object put", backup)
        self.assertNotIn("bootstrap", backup.casefold())
        self.assertNotIn("continue-on-error: true", backup)
        self.assertNotIn("git add feeds cache", commit)
        self.assertIn("git add feeds docs/sources.md", commit)
        self.assertIn("steps.backup.outcome == 'success'", commit)


    def test_live_pages_are_built_from_generated_files(self):
        workflow = self.workflow()
        self.assertIn("uses: actions/upload-pages-artifact@", workflow)
        self.assertIn("uses: actions/deploy-pages@", workflow)
        self.assertIn("needs: update-feeds", workflow)
        self.assertLess(
            workflow.index("- name: Back up Feedseek cache to R2"),
            workflow.index("- name: Build live Pages site"),
        )
        self.assertLess(
            workflow.index("- name: Upload live Pages artifact"),
            workflow.index("- name: Commit and push successful updates"),
        )
        self.assertIn("pages: write", workflow)
        self.assertIn("id-token: write", workflow)

    def test_git_snapshot_is_periodic_but_manual_and_push_runs_still_commit(self):
        workflow = self.workflow()
        snapshot = workflow.split("- name: Decide whether Git snapshot is due", 1)[1]
        snapshot = snapshot.split("- name: Commit and push successful updates", 1)[0]
        commit = workflow.split("- name: Commit and push successful updates", 1)[1]
        commit = commit.split("- name: Apply feed health gate", 1)[0]
        self.assertIn('FEEDSEEK_GIT_SNAPSHOT_HOURS: "6"', workflow)
        self.assertIn('"$GITHUB_EVENT_NAME" != "schedule"', snapshot)
        self.assertIn("commits?path=feeds&per_page=1", snapshot)
        self.assertIn("echo \"due=true\"", snapshot)
        self.assertIn("steps.snapshot.outputs.due == 'true'", commit)
        self.assertIn("steps.pages_upload.outcome == 'success'", commit)

    def test_only_update_feeds_auto_deploys_production(self):
        deploy = (Path(__file__).resolve().parents[1] / ".github" / "workflows" / "deploy-pages.yml").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("workflow_run:", deploy)
        self.assertNotIn("  push:", deploy)
        self.assertIn("  workflow_dispatch:", deploy)
        self.assertIn("github.event_name == 'workflow_dispatch'", deploy)
        self.assertIn("group: feedseek-pages-deploy", deploy)

if __name__ == "__main__":
    unittest.main()
