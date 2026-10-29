import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))

import microsoft_updates  # noqa: E402

SERVICING_NAV = """
<ul>
  <li><a href="../10/kb5134134-windows-11-26h1-update" class="learnRenderLeftNavLink">
    October 26, 2026—KB55134134 (OS Build 28000.3237) Out-of-band</a></li>
  <li><a href="../../2026/10/kb5126657-windows-10-21h2-22h2-security-update" class="learnRenderLeftNavLink">
    October 13, 2026—KB5126657 (OS Builds 19045.7807 and 19044.7807)</a></li>
  <li><a href="../10/overview" class="learnRenderLeftNavLink">Windows 11 overview</a></li>
</ul>
"""


class UpdateHistoryLayoutTests(unittest.TestCase):
    def test_servicing_layout_yields_canonical_help_links(self):
        with patch.object(microsoft_updates, "get_html", return_value=SERVICING_NAV):
            entries = microsoft_updates._scrape_update_history("Windows 11 updates", "https://x", set())

        self.assertEqual(
            [entry["link"] for entry in entries],
            [
                "https://support.microsoft.com/en-us/help/5134134",
                "https://support.microsoft.com/en-us/help/5126657",
            ],
        )
        self.assertEqual(entries[0]["date"].date().isoformat(), "2026-10-26")


if __name__ == "__main__":
    unittest.main()
