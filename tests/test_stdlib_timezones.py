import re
import tomllib
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]


class StdlibTimezoneTests(unittest.TestCase):
    def test_project_uses_zoneinfo_without_pytz_dependency(self):
        data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        dependencies = data["project"]["dependencies"]
        self.assertFalse(any(dep.lower().startswith("pytz") for dep in dependencies))
        self.assertTrue(any(dep.lower().startswith("tzdata") for dep in dependencies))

    def test_python_sources_do_not_import_pytz(self):
        offenders = []
        for folder in (ROOT / "feed_generators", ROOT / "tests"):
            for path in folder.rglob("*.py"):
                if path == Path(__file__).resolve():
                    continue
                text = path.read_text(encoding="utf-8")
                if re.search(r"(?m)^\s*(?:import\s+pytz\b|from\s+pytz\b)", text):
                    offenders.append(str(path.relative_to(ROOT)))
        self.assertEqual(offenders, [])

    def test_warsaw_zoneinfo_has_winter_and_summer_offsets(self):
        warsaw = ZoneInfo("Europe/Warsaw")
        self.assertEqual(datetime(2026, 1, 15, 12, tzinfo=warsaw).utcoffset().total_seconds(), 3600)
        self.assertEqual(datetime(2026, 7, 15, 12, tzinfo=warsaw).utcoffset().total_seconds(), 7200)

    def test_imgw_ambiguous_wall_time_keeps_pytz_standard_time_choice(self):
        import sys

        sys.path.insert(0, str(ROOT / "feed_generators"))
        import imgw

        parsed = imgw.parse_pl_datetime("2026-10-25 02:30:00")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.utcoffset().total_seconds(), 3600)


if __name__ == "__main__":
    unittest.main()
