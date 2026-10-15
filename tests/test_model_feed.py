import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))

from jsonfeed import _entry_content
from model_feed import (
    MODEL_FEED_FORMAT,
    MODEL_FEED_VERSION,
    build_model_feed,
    write_all_model_feeds,
)


class JsonFeedTextSemanticsTests(unittest.TestCase):
    def test_html_mislabeled_as_plain_text_is_promoted(self):
        key, value, kind = _entry_content(
            {
                "content": [
                    {
                        "type": "text/plain",
                        "value": '<a href="https://example.com">Story</a> <font>Source</font>',
                    }
                ]
            }
        )
        self.assertEqual(key, "content_html")
        self.assertEqual(kind, "content")
        self.assertIn("<a ", value)

    def test_text_like_angle_brackets_stay_plain_text(self):
        key, value, kind = _entry_content(
            {
                "content": [
                    {
                        "type": "text/plain",
                        "value": "Use List<T> when x < y and z > q.",
                    }
                ]
            }
        )
        self.assertEqual(key, "content_text")
        self.assertEqual(value, "Use List<T> when x < y and z > q.")
        self.assertEqual(kind, "content")

    def test_missing_body_falls_back_to_title(self):
        self.assertEqual(
            _entry_content({"title": "Title only"}),
            ("content_text", "Title only", "title"),
        )


class ModelFeedTests(unittest.TestCase):
    def test_model_feed_is_plaintext_and_keeps_reasoning_metadata(self):
        doc = build_model_feed(
            {
                "title": "Demo",
                "feed_url": "https://example.com/feed.json",
                "home_page_url": "https://example.com/",
                "items": [
                    {
                        "id": "one",
                        "url": "https://example.com/one",
                        "title": "One",
                        "content_html": (
                            "<p>Hello &amp; <strong>world</strong>.</p>"
                            "<script>ignore()</script><p>Second line.</p>"
                        ),
                        "_feedseek": {"textKind": "summary"},
                        "date_published": "2026-10-15T10:00:00Z",
                        "authors": [{"name": "Example"}],
                        "tags": ["AI"],
                        "image": "https://example.com/image.jpg",
                    }
                ],
            },
            "demo",
        )

        self.assertEqual(doc["format"], MODEL_FEED_FORMAT)
        self.assertEqual(doc["version"], MODEL_FEED_VERSION)
        self.assertEqual(doc["source_key"], "demo")
        item = doc["items"][0]
        self.assertEqual(item["text"], "Hello & world.\n\nSecond line.")
        self.assertEqual(item["text_kind"], "summary")
        self.assertEqual(item["authors"], ["Example"])
        self.assertEqual(item["tags"], ["AI"])
        self.assertNotIn("content_html", item)

    def test_escaped_markup_inside_html_stays_visible(self):
        doc = build_model_feed(
            {
                "title": "Demo",
                "items": [
                    {
                        "id": "one",
                        "title": "Code sample",
                        "content_html": (
                            "<pre>&lt;script&gt;keep()&lt;/script&gt;</pre>"
                        ),
                        "_feedseek": {"textKind": "content"},
                    }
                ],
            },
            "demo",
        )
        self.assertEqual(
            doc["items"][0]["text"],
            "<script>keep()</script>",
        )

    def test_definition_lists_keep_field_boundaries(self):
        doc = build_model_feed(
            {
                "title": "Demo",
                "items": [
                    {
                        "id": "one",
                        "title": "Definitions",
                        "content_html": "<dl><dt>Term</dt><dd>Definition</dd></dl>",
                        "_feedseek": {"textKind": "content"},
                    }
                ],
            },
            "demo",
        )
        self.assertEqual(doc["items"][0]["text"], "Term\n\nDefinition")

    def test_preformatted_content_keeps_indentation(self):
        doc = build_model_feed(
            {
                "title": "Demo",
                "items": [
                    {
                        "id": "one",
                        "title": "Code",
                        "content_html": "<pre>if ready:\n    deploy()</pre>",
                        "_feedseek": {"textKind": "content"},
                    }
                ],
            },
            "demo",
        )
        self.assertEqual(doc["items"][0]["text"], "if ready:\n    deploy()")

    def test_plaintext_escaped_markup_stays_visible(self):
        doc = build_model_feed(
            {
                "title": "Demo",
                "items": [
                    {
                        "id": "one",
                        "title": "Literal",
                        "content_text": "Use &lt;script&gt;keep()&lt;/script&gt;",
                        "_feedseek": {"textKind": "content"},
                    }
                ],
            },
            "demo",
        )
        self.assertEqual(
            doc["items"][0]["text"],
            "Use <script>keep()</script>",
        )

    def test_nested_entities_are_decoded_once(self):
        doc = build_model_feed(
            {
                "title": "Demo",
                "items": [
                    {
                        "id": "one",
                        "title": "Entities",
                        "content_html": "<p>&amp;amp; &amp;lt;</p>",
                        "_feedseek": {"textKind": "content"},
                    }
                ],
            },
            "demo",
        )
        self.assertEqual(doc["items"][0]["text"], "&amp; &lt;")

    def test_model_feed_cleans_html_hidden_in_content_text(self):
        doc = build_model_feed(
            {
                "title": "Demo",
                "items": [
                    {
                        "id": "one",
                        "title": "Story",
                        "content_text": (
                            '<a href="https://example.com">Story</a>&nbsp;'
                            '<font color="#666">Reuters</font>'
                        ),
                    }
                ],
            },
            "demo",
        )
        self.assertEqual(doc["items"][0]["text"], "Story Reuters")

    def test_backfill_ignores_existing_model_sidecars(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "feed_demo.json").write_text(
                json.dumps(
                    {
                        "version": "https://jsonfeed.org/version/1.1",
                        "title": "Demo",
                        "items": [
                            {
                                "id": "one",
                                "title": "One",
                                "content_text": "Hello",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (root / "feed_existing.model.json").write_text("{}", encoding="utf-8")

            count = write_all_model_feeds(root)

            self.assertEqual(count, 1)
            generated = json.loads(
                (root / "feed_demo.model.json").read_text(encoding="utf-8")
            )
            self.assertEqual(generated["format"], MODEL_FEED_FORMAT)
            self.assertEqual(generated["items"][0]["text"], "Hello")


if __name__ == "__main__":
    unittest.main()
