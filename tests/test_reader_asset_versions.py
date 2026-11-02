import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = Path(__file__).resolve().parents[1] / "site" / "build_site.py"
SPEC = importlib.util.spec_from_file_location("build_site", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load {MODULE_PATH}")
build_site = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_site)


class ReaderAssetVersionTests(unittest.TestCase):
    def test_script_versions_follow_asset_contents(self):
        with tempfile.TemporaryDirectory() as tmp:
            site_dir = Path(tmp)
            (site_dir / "reader.html").write_text(
                '<script src="reader-fetch.js"></script><script src="reader.js"></script>'
                '<script src="../webmcp.js"></script>',
                encoding="utf-8",
            )
            fetch_script = site_dir / "reader-fetch.js"
            fetch_script.write_bytes(b"fetch v1")
            script = site_dir / "reader.js"
            script.write_bytes(b"reader v1")
            webmcp_script = site_dir / "webmcp.js"
            webmcp_script.write_bytes(b"webmcp v1")
            with patch.object(build_site, "SITE_DIR", site_dir):
                first = build_site.build_reader_html("https://example.test/")
                script.write_bytes(b"reader v2")
                second = build_site.build_reader_html("https://example.test/")
                fetch_script.write_bytes(b"fetch v2")
                webmcp_script.write_bytes(b"webmcp v2")
                third = build_site.build_reader_html("https://example.test/")

            fetch_version = hashlib.sha256(b"fetch v1").hexdigest()[:12]
            new_fetch_version = hashlib.sha256(b"fetch v2").hexdigest()[:12]
            old_version = hashlib.sha256(b"reader v1").hexdigest()[:12]
            new_version = hashlib.sha256(b"reader v2").hexdigest()[:12]
            webmcp_version = hashlib.sha256(b"webmcp v1").hexdigest()[:12]
            new_webmcp_version = hashlib.sha256(b"webmcp v2").hexdigest()[:12]
            self.assertIn(f'src="reader-fetch.js?v={fetch_version}"', first)
            self.assertIn(f'src="reader-fetch.js?v={fetch_version}"', second)
            self.assertIn(f'src="reader-fetch.js?v={new_fetch_version}"', third)
            self.assertIn(f'src="reader.js?v={old_version}"', first)
            self.assertIn(f'src="reader.js?v={new_version}"', second)
            self.assertIn(f'src="reader.js?v={new_version}"', third)
            self.assertIn(f'src="../webmcp.js?v={webmcp_version}"', first)
            self.assertIn(f'src="../webmcp.js?v={webmcp_version}"', second)
            self.assertIn(f'src="../webmcp.js?v={new_webmcp_version}"', third)


if __name__ == "__main__":
    unittest.main()
