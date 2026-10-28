import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))

import docs_model_feeds as index
import model_feed


class ModelFeedIndexTests(unittest.TestCase):
    def write_feed(self, directory, key, title, count):
        payload = {
            "format": "feedseek-model-feed",
            "version": 1,
            "source_key": key,
            "title": title,
            "items": [{"id": str(i), "text": "Article body stays in JSON"} for i in range(count)],
        }
        (directory / f"feed_{key}.json").write_text(json.dumps(payload), encoding="utf-8")

    def test_indexes_all_existing_json_without_a_registry_or_public_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            feeds = Path(tmp)
            self.write_feed(feeds, "unlisted", "Beta", 2)
            self.write_feed(feeds, "alpha", "Alpha | [link]\n<script>", 3)
            markdown = index.build_markdown(feeds, "owner/repo")
            self.assertIn("2 Model Feeds · 5 entries.", markdown)
            self.assertLess(markdown.index("| `alpha`"), markdown.index("| `unlisted`"))
            self.assertIn("Alpha \\| \\[link\\] \\<script\\>", markdown)
            self.assertIn(
                "https://raw.githubusercontent.com/owner/repo/main/feeds/feed_unlisted.json",
                markdown,
            )
            self.assertNotIn("Article body stays in JSON", markdown)
            self.assertEqual(markdown, index.build_markdown(feeds, "owner/repo"))

    def test_empty_or_invalid_input_preserves_last_good_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            feeds = root / "feeds"
            feeds.mkdir()
            out = root / "model-feeds.md"
            out.write_text("last good", encoding="utf-8")
            for invalid in (
                None,
                "broken json",
                "[]",
                "{}",
                '{"format":"feedseek-model-feed","version":1,"items":{}}',
            ):
                if invalid is not None:
                    (feeds / "feed_bad.json").write_text(invalid, encoding="utf-8")
                with self.assertRaises(ValueError):
                    index.write_index(feeds, out)
                self.assertEqual(out.read_text(encoding="utf-8"), "last good")

    def test_check_detects_drift_without_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            feeds = root / "feeds"
            feeds.mkdir()
            self.write_feed(feeds, "demo", "Demo", 1)
            out = root / "model-feeds.md"
            index.write_index(feeds, out)
            with (
                patch.object(index, "FEEDS_DIR", feeds),
                patch.object(index, "OUT", out),
                patch.object(sys, "argv", ["docs_model_feeds.py", "--check"]),
            ):
                self.assertEqual(index.main(), 0)
                self.write_feed(feeds, "new", "New", 2)
                before = out.read_bytes()
                self.assertEqual(index.main(), 1)
                self.assertEqual(out.read_bytes(), before)

    def test_model_refresh_updates_index_from_new_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            feeds = root / "feeds"
            feeds.mkdir()
            (feeds / "feed_demo.xml").write_text(
                '<feed xmlns="http://www.w3.org/2005/Atom"><id>demo</id><title>Demo</title>'
                "<updated>2026-10-28T00:00:00Z</updated><entry><id>one</id><title>One</title>"
                "<updated>2026-10-28T00:00:00Z</updated><summary>Body</summary></entry></feed>",
                encoding="utf-8",
            )
            out = root / "docs" / "model-feeds.md"
            with patch.object(model_feed, "__file__", str(root / "feed_generators" / "model_feed.py")):
                model_feed.main()
            self.assertTrue((feeds / "feed_demo.json").is_file())
            self.assertIn("1 Model Feeds · 1 entries.", out.read_text(encoding="utf-8"))
            self.assertIn("feed_demo.json", out.read_text(encoding="utf-8"))

    def test_push_retry_regenerates_index_after_concurrent_feed_addition(self):
        root = Path(__file__).resolve().parents[1]
        workflow = yaml.safe_load((root / ".github/workflows/update-feeds.yml").read_text())
        script = next(
            step["run"]
            for step in workflow["jobs"]["update-feeds"]["steps"]
            if step["name"] == "Commit and push successful updates"
        ).replace("uv run --locked", shlex.quote(sys.executable))
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            origin, seed, job = (base / name for name in ("origin.git", "seed", "job"))
            env = {**os.environ, "GIT_CONFIG_GLOBAL": str(base / "gitconfig")}

            def run(cwd, *args):
                result = subprocess.run(args, cwd=cwd, env=env, check=False, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, f"{args}:\n{result.stdout}\n{result.stderr}")
                return result

            run(base, "git", "config", "--global", "user.name", "Index test")
            run(base, "git", "config", "--global", "user.email", "index@example.test")
            run(base, "git", "init", "--bare", "--initial-branch=main", str(origin))
            run(base, "git", "init", "--initial-branch=main", str(seed))
            shutil.copyfile(root / ".gitignore", seed / ".gitignore")
            (seed / "feeds").mkdir()
            (seed / "docs").mkdir()
            (seed / "docs/sources.md").write_text("Sources\n")
            (seed / "feed_generators").mkdir()
            for name in ("docs_model_feeds.py", "utils.py"):
                shutil.copyfile(root / "feed_generators" / name, seed / "feed_generators" / name)
            self.write_feed(seed / "feeds", "alpha", "Alpha", 1)
            run(seed, sys.executable, "feed_generators/docs_model_feeds.py")
            run(seed, "git", "add", ".")
            run(seed, "git", "commit", "-m", "Initial feed")
            self.assertNotIn("__pycache__", run(seed, "git", "ls-files").stdout)
            run(seed, "git", "remote", "add", "origin", str(origin))
            run(seed, "git", "push", "-u", "origin", "main")
            run(base, "git", "clone", str(origin), str(job))
            os.utime(job / "feed_generators/utils.py", (1, 1))

            self.write_feed(job / "feeds", "alpha", "Alpha", 2)
            run(job, sys.executable, "feed_generators/docs_model_feeds.py")
            self.write_feed(seed / "feeds", "beta", "Beta", 7)
            run(seed, "git", "add", ".")
            run(seed, "git", "commit", "-m", "Concurrent feed addition")
            run(seed, "git", "push")

            run(job, "bash", "-euo", "pipefail", "-c", script)
            markdown = (job / "docs/model-feeds.md").read_text()
            self.assertIn("2 Model Feeds · 9 entries.", markdown)
            self.assertIn("feed_beta.json", markdown)
            self.assertEqual(run(job, "git", "status", "--porcelain").stdout, "")
            self.assertEqual(
                run(job, "git", "rev-parse", "HEAD").stdout, run(job, "git", "rev-parse", "origin/main").stdout
            )


if __name__ == "__main__":
    unittest.main()
