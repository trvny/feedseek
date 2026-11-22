import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "site" / "build_site.py"
SPEC = importlib.util.spec_from_file_location("build_site", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Cannot load {MODULE_PATH}")
build_site = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_site)


class AgentDiscoveryTests(unittest.TestCase):
    def test_ard_manifest_and_card_reference_real_mcp(self):
        base = "https://rss.bartek.lol/"
        catalog = build_site.build_agent_catalog(base)
        self.assertEqual(catalog["specVersion"], "0.9")
        self.assertEqual(catalog["host"]["identifier"], "rss.bartek.lol")
        self.assertEqual(len(catalog["entries"]), 2)
        self.assertEqual(len({e["identifier"] for e in catalog["entries"]}), 2)
        for entry in catalog["entries"]:
            self.assertTrue(entry["identifier"].startswith("urn:air:rss.bartek.lol:"))
            self.assertEqual(entry["@context"], "https://agenticresourcediscovery.org/context/v1")
            self.assertEqual(entry["url"].startswith(base), True)
            self.assertNotIn("data", entry)
            self.assertGreaterEqual(len(entry["representativeQueries"]), 2)

        card = build_site.build_mcp_server_card()
        self.assertEqual(catalog["entries"][0]["type"], "application/mcp-server-card+json")
        self.assertEqual(catalog["entries"][0]["url"], base + ".well-known/mcp/server-card.json")
        self.assertEqual(card["name"], "feedseek")
        self.assertEqual(card["remotes"][0]["url"], base + "mcp")
        self.assertEqual(card["$schema"], "https://raw.githubusercontent.com/modelcontextprotocol/ext-server-card/main/schema.json")
        self.assertEqual(card["remotes"][0]["type"], "streamable-http")
        self.assertIn("2026-07-28", card["remotes"][0]["supportedProtocolVersions"])
        self.assertEqual(catalog["entries"][1]["url"], base + "model-feeds.json")

    def test_hidden_files_survive_artifact_upload(self):
        import re
        for name in ("update-feeds.yml", "deploy-pages.yml"):
            workflow = (MODULE_PATH.parent.parent / ".github" / "workflows" / name).read_text(encoding="utf-8")
            self.assertRegex(workflow, r"(?m)^\s*include-hidden-files: true$")

    def test_page_links_and_guides_reference_ard(self):
        html = build_site.build_index([], "https://rss.bartek.lol/")
        self.assertIn('rel="ard"', html)
        self.assertIn(".well-known/ard.json", html)
        guide = build_site.build_llms_txt([], "https://rss.bartek.lol/")
        self.assertIn("https://rss.bartek.lol/.well-known/ard.json", guide)
        reader = (MODULE_PATH.parent / "reader.html").read_text(encoding="utf-8")
        self.assertIn('rel="ard"', reader)


if __name__ == "__main__":
    unittest.main()
