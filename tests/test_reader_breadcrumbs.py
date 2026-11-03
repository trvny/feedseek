import importlib.util
import json
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "site" / "build_site.py"
SPEC = importlib.util.spec_from_file_location("build_site", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load {MODULE_PATH}")
build_site = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_site)


class ReaderBreadcrumbTests(unittest.TestCase):
    def test_reader_breadcrumbs_match_custom_canonical_base(self):
        base = "https://example.org/feeds/"
        html = build_site.build_reader_html(base)
        schemas = [
            json.loads(block.split("</script>", 1)[0])
            for block in html.split('<script type="application/ld+json">')[1:]
        ]
        matching = [schema for schema in schemas if schema.get("@type") == "BreadcrumbList"]
        self.assertEqual(len(matching), 1)
        crumbs = matching[0]
        self.assertEqual(
            [(item["position"], item["name"], item["item"]) for item in crumbs["itemListElement"]],
            [
                (1, "Feedseek", base),
                (2, "Reader", f"{base}reader/"),
            ],
        )
        self.assertIn(f'<link rel="canonical" href="{base}reader/">', html)
        self.assertIn('<nav class="crumb" aria-label="Breadcrumb">', html)
        self.assertIn('<a href="../">Feedseek</a>', html)
        self.assertIn('<span aria-current="page">Reader</span>', html)


if __name__ == "__main__":
    unittest.main()
