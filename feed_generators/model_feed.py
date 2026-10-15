"""Feedseek Model Feed writer.

Model Feeds are compact, plaintext-oriented JSON sidecars derived from the
standard JSON Feed 1.1 publication artifact. They are intentionally optimized
for model/agent consumption rather than RSS reader compatibility.

Schema v1 keeps only citation- and reasoning-relevant fields:
- durable id and canonical URL,
- title plus normalized plaintext,
- text_kind (content, summary, or title),
- publication/update timestamps,
- authors, tags, and an optional representative image.

The standard JSON Feed remains the maintained machine-readable source. Model
Feeds are a deterministic adapter over it, not a second editorial pipeline.
"""

from __future__ import annotations

import json
from pathlib import Path

from html_text import plain_text
from utils import REPO_SLUG, write_atomically

MODEL_FEED_FORMAT = "feedseek-model-feed"
MODEL_FEED_VERSION = 1
_MODEL_FEED_URL_TMPL = (
    f"https://raw.githubusercontent.com/{REPO_SLUG}/main/feeds/"
    "feed_{name}.model.json"
)

def _text_kind(item: dict) -> str:
    extension = item.get("_feedseek")
    if isinstance(extension, dict):
        kind = extension.get("textKind", extension.get("text_kind"))
        if isinstance(kind, str) and kind in {"content", "summary", "title"}:
            return kind
    if isinstance(item.get("content_html"), str) and item["content_html"].strip():
        return "content"
    if isinstance(item.get("content_text"), str) and item["content_text"].strip():
        return "content"
    if isinstance(item.get("summary"), str) and item["summary"].strip():
        return "summary"
    return "title"


def _item_text(item: dict) -> tuple[str, str]:
    kind = _text_kind(item)

    if isinstance(item.get("content_text"), str) and item["content_text"].strip():
        text = plain_text(item["content_text"])
    elif isinstance(item.get("content_html"), str) and item["content_html"].strip():
        text = plain_text(item["content_html"], html_hint=True)
    elif isinstance(item.get("summary"), str) and item["summary"].strip():
        text = plain_text(item["summary"])
        kind = "summary"
    else:
        text = plain_text(item.get("title"))
        kind = "title"

    if not text:
        text = plain_text(item.get("title"))
        kind = "title"
    return text, kind


def build_model_feed(json_feed: dict, feed_name: str) -> dict:
    """Return a Feedseek Model Feed v1 document from a JSON Feed 1.1 dict."""
    doc: dict = {
        "format": MODEL_FEED_FORMAT,
        "version": MODEL_FEED_VERSION,
        "source_key": feed_name,
        "title": str(json_feed.get("title") or feed_name),
        "feed_url": _MODEL_FEED_URL_TMPL.format(name=feed_name),
        "source_feed": str(json_feed.get("feed_url") or ""),
    }
    for key in ("home_page_url", "description"):
        value = json_feed.get(key)
        if isinstance(value, str) and value.strip():
            doc[key] = value

    items: list[dict] = []
    for raw in json_feed.get("items") or []:
        if not isinstance(raw, dict):
            continue
        item_id = raw.get("id")
        if not isinstance(item_id, str) or not item_id:
            continue

        text, text_kind = _item_text(raw)
        item: dict = {
            "id": item_id,
            "title": str(raw.get("title") or ""),
            "text": text,
            "text_kind": text_kind,
        }

        for key in ("url", "external_url"):
            value = raw.get(key)
            if isinstance(value, str) and value.strip():
                item[key] = value

        if isinstance(raw.get("date_published"), str):
            item["date_published"] = raw["date_published"]
        if isinstance(raw.get("date_modified"), str):
            item["date_modified"] = raw["date_modified"]

        authors = raw.get("authors")
        if isinstance(authors, list):
            names = [
                author.get("name")
                for author in authors
                if isinstance(author, dict)
                and isinstance(author.get("name"), str)
                and author["name"].strip()
            ]
            if names:
                item["authors"] = names

        tags = raw.get("tags")
        if isinstance(tags, list):
            clean_tags = [
                tag for tag in tags if isinstance(tag, str) and tag.strip()
            ]
            if clean_tags:
                item["tags"] = clean_tags

        image = raw.get("image")
        if isinstance(image, str) and image.strip():
            item["image"] = image

        items.append(item)

    doc["items"] = items
    return doc


def load_json_feed(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        raise ValueError(f"Invalid JSON Feed document: {path}")
    return data


def write_model_feed(
    json_path: Path,
    feed_name: str,
    *,
    output_path: Path | None = None,
) -> Path:
    """Write a deterministic ``feed_<name>.model.json`` sidecar."""
    doc = build_model_feed(load_json_feed(json_path), feed_name)
    out = output_path or json_path.with_name(f"feed_{feed_name}.model.json")
    payload = json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n"
    write_atomically(out, lambda target: target.write_text(payload, encoding="utf-8"))
    return out


def write_all_model_feeds(feeds_dir: Path) -> int:
    """Regenerate model sidecars for every standard JSON Feed in a directory."""
    count = 0
    for json_path in sorted(feeds_dir.glob("feed_*.json")):
        if json_path.name.endswith(".model.json"):
            continue
        feed_name = json_path.stem.removeprefix("feed_")
        write_model_feed(json_path, feed_name)
        count += 1
    return count


def main() -> None:
    feeds_dir = Path(__file__).resolve().parents[1] / "feeds"
    count = write_all_model_feeds(feeds_dir)
    print(f"Built {count} Feedseek Model Feed sidecars in {feeds_dir}")


if __name__ == "__main__":
    main()
