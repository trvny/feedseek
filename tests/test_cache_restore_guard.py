import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))

import utils


class CacheRestoreGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cache_dir = Path(self.tmp.name)
        self.generator = Path(utils.__file__).with_name("daily_quote.py")

    def test_direct_incremental_generator_requires_fresh_restore(self):
        with (
            mock.patch.object(utils, "get_cache_dir", return_value=self.cache_dir),
            mock.patch.object(sys, "argv", [str(self.generator)]),
            mock.patch.dict(os.environ, {}, clear=False),
        ):
            os.environ.pop("FEEDSEEK_CACHE_RESTORED", None)
            with self.assertRaises(RuntimeError):
                utils.load_cache("demo")

    def test_direct_generator_consumes_one_shot_restore_marker(self):
        marker = self.cache_dir / ".r2-restored"
        marker.write_text("restored\n", encoding="utf-8")
        (self.cache_dir / "demo_posts.json").write_text(
            json.dumps({"entries": [{"id": "one"}]}), encoding="utf-8"
        )
        with (
            mock.patch.object(utils, "get_cache_dir", return_value=self.cache_dir),
            mock.patch.object(sys, "argv", [str(self.generator)]),
            mock.patch.dict(os.environ, {}, clear=False),
        ):
            os.environ.pop("FEEDSEEK_CACHE_RESTORED", None)
            data = utils.load_cache("demo")
            self.assertEqual(data["entries"], [{"id": "one"}])
            self.assertFalse(marker.exists())
            self.assertEqual(os.environ["FEEDSEEK_CACHE_RESTORED"], "1")
            os.environ.pop("FEEDSEEK_CACHE_RESTORED", None)

    def test_full_direct_generator_does_not_require_restore(self):
        with (
            mock.patch.object(utils, "get_cache_dir", return_value=self.cache_dir),
            mock.patch.object(sys, "argv", [str(self.generator), "--full"]),
        ):
            self.assertEqual(utils.load_cache("demo")["entries"], [])


if __name__ == "__main__":
    unittest.main()
