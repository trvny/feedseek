"""Published Model Feed JSON Schema stays in step with builder, validator and outputs."""

import json
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "feed_generators"))

from model_feed import MODEL_FEED_FORMAT, MODEL_FEED_VERSION, build_model_feed

SCHEMA_PATH = ROOT / "docs" / "schemas" / "model-feed.v1.schema.json"


def _validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)


class ModelFeedSchemaTests(unittest.TestCase):
    validator = _validator()

    def errors(self, doc: dict) -> list[str]:
        return [error.message for error in self.validator.iter_errors(doc)]

    def built_doc(self) -> dict:
        return build_model_feed(
            {
                "title": "Example",
                "home_page_url": "https://example.com/",
                "description": "Example feed",
                "items": [
                    {
                        "id": "tag:trvny.github.io,2024:feedseek/example/1",
                        "title": "Full",
                        "content_html": "<p>Body</p>",
                        "url": "https://example.com/1",
                        "date_published": "2026-10-28T16:19:10Z",
                        "date_modified": "2026-10-28T16:19:10+00:00",
                        "authors": [{"name": "Ann"}],
                        "tags": ["News"],
                        "image": "https://example.com/1.png",
                    },
                    {"id": "tag:trvny.github.io,2024:feedseek/example/2", "title": "Title only"},
                ],
            },
            "example",
        )

    def test_schema_constants_match_builder(self):
        props = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))["properties"]
        self.assertEqual(props["format"]["const"], MODEL_FEED_FORMAT)
        self.assertEqual(props["version"]["const"], MODEL_FEED_VERSION)

    def test_builder_output_matches_schema(self):
        self.assertEqual(self.errors(self.built_doc()), [])

    def test_committed_model_feeds_match_schema(self):
        paths = sorted((ROOT / "feeds").glob("feed_*.json"))
        self.assertTrue(paths)
        for path in paths:
            with self.subTest(feed=path.name):
                doc = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(self.errors(doc)[:3], [])

    def test_rejects_validator_failures(self):
        cases = {
            "version": lambda d: d.update(version=2),
            "blank id": lambda d: d["items"][0].update(id="  "),
            "blank text": lambda d: d["items"][0].update(text=" \n"),
            "text_kind": lambda d: d["items"][0].update(text_kind="html"),
            "unknown field": lambda d: d["items"][0].update(content_html="<p>x</p>"),
            "bad date": lambda d: d["items"][0].update(date_published="yesterday"),
        }
        for name, mutate in cases.items():
            with self.subTest(case=name):
                doc = self.built_doc()
                mutate(doc)
                self.assertNotEqual(self.errors(doc), [])


if __name__ == "__main__":
    unittest.main()
