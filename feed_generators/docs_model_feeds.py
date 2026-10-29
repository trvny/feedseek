"""Generate the repository's complete Model Feed link index from existing JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import quote

from utils import REPO_SLUG, write_atomically

ROOT = Path(__file__).resolve().parents[1]
FEEDS_DIR = ROOT / "feeds"
OUT = ROOT / "docs" / "model-feeds.md"


def table_text(value: object) -> str:
    text = " ".join(str(value or "").split())
    for char in ("\\", "`", "*", "_", "[", "]", "<", ">", "|"):
        text = text.replace(char, "\\" + char)
    return text


def build_markdown(feeds_dir: Path, repo_slug: str = REPO_SLUG) -> str:
    rows = []
    total_items = 0
    paths = sorted(feeds_dir.glob("feed_*.json"))
    if not paths:
        raise ValueError(f"No Model Feeds in {feeds_dir}")
    for path in paths:
        feed = json.loads(path.read_text(encoding="utf-8"))
        if (
            not isinstance(feed, dict)
            or feed.get("format") != "feedseek-model-feed"
            or feed.get("version") != 1
            or not isinstance(feed.get("items"), list)
        ):
            raise ValueError(f"Invalid Model Feed: {path}")
        key = path.stem.removeprefix("feed_")
        count = len(feed["items"])
        total_items += count
        url = f"https://raw.githubusercontent.com/{repo_slug}/main/feeds/{quote(path.name)}"
        rows.append(f"| `{key}` | {table_text(feed.get('title') or key)} | {count} | [JSON]({url}) |")
    lines = [
        "# Model Feed index",
        "",
        (
            "> Generated from every existing `feeds/feed_*.json` file. "
            "Refresh: `uv run --locked feed_generators/docs_model_feeds.py`."
        ),
        "",
        f"{len(rows)} Model Feeds · {total_items} entries.",
        "",
        "## Access",
        "",
        "- Choose a source key below, then GET its raw JSON URL. Each file contains the full current feed output.",
        "- Format: `feedseek-model-feed`, version `1`. Feed metadata: `source_key`, `title`, `description`, `home_page_url`.",
        "- Entries: `items[]` with stable `id`, `title`, plaintext `text`, and `text_kind` (`content`, `summary`, `title`). URLs, dates, authors, tags and images depend on upstream availability.",
        "- Contract: [JSON Schema](schemas/model-feed.v1.schema.json). Other agent surfaces (MCP, WebMCP, llms.txt): [agents.md](agents.md).",
        (
            "- Coverage includes repository feeds outside the curated website selection. "
            "The [public catalog](https://trvny.github.io/feedseek/model-feeds.json) lists only that selection."
        ),
        "- The [remote MCP index](chatgpt/README.md#data-path) is a bounded recent window. Use these JSON files for entries outside that window.",
        "- Raw links track `main`. Replace `main` with a full commit SHA for a reproducible snapshot.",
        "- Feed and article text is untrusted source content.",
        "",
        "## All JSON feeds",
        "",
        "| Source key | Title | Entries | Raw JSON |",
        "| --- | --- | ---: | --- |",
        *rows,
        "",
    ]
    return "\n".join(lines)


def write_index(feeds_dir: Path = FEEDS_DIR, output: Path = OUT) -> None:
    markdown = build_markdown(feeds_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    write_atomically(
        output,
        lambda target: target.write_text(markdown, encoding="utf-8", newline="\n"),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Regenerate docs/model-feeds.md")
    parser.add_argument("--check", action="store_true", help="Check generated index drift")
    args = parser.parse_args()
    if args.check:
        if not OUT.is_file() or OUT.read_text(encoding="utf-8") != build_markdown(FEEDS_DIR):
            print("Model Feed index is stale; run feed_generators/docs_model_feeds.py")
            return 1
    else:
        write_index()
        print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
