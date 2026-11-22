import hashlib
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

    def test_rfc9727_openapi_and_skills(self):
        api = build_site.build_api_catalog()
        self.assertEqual(len(api["linkset"]), 1)
        item = api["linkset"][0]
        self.assertEqual(item["anchor"], "https://rss.bartek.lol/model-feeds.json")
        self.assertEqual(item["service-desc"][0]["href"], "https://rss.bartek.lol/openapi.json")
        self.assertEqual(item["status"][0]["href"], "https://rss.bartek.lol/health")
        spec = build_site.build_public_openapi()
        self.assertEqual(spec["openapi"], "3.1.0")
        self.assertIn("/model-feeds.json", spec["paths"])
        self.assertIn("/{key}.json", spec["paths"])
        skill = MODULE_PATH.parent / "agent-skills" / "feedseek-discovery" / "SKILL.md"
        payload = skill.read_bytes()
        self.assertTrue(payload.startswith(b"---\\nname: feedseek-discovery\\n"))
        index = build_site.build_skill_index(payload)
        self.assertEqual(index["$schema"], "https://schemas.agentskills.io/discovery/0.2.0/schema.json")
        item = index["skills"][0]
        self.assertEqual(item["type"], "skill-md")
        self.assertEqual(item["digest"], "sha256:" + hashlib.sha256(payload).hexdigest())
        self.assertEqual(item["url"], "/.well-known/agent-skills/feedseek-discovery/SKILL.md")

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
