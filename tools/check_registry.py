"""Strict feeds.yaml check: fails on YAML errors, skipped entries or a bad published_feeds list.

The runtime loader is lenient (skips broken entries); this gate is not, so a typo
fails fast in MegaLinter CI instead of surfacing hours later in Update Feeds.
"""

import os
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))

import models  # noqa: E402


def check(path: Path | None = None) -> list[str]:
    if path is not None:
        models.REGISTRY_PATH = path
    try:
        feeds, skipped = models.load_feed_registry(return_skipped=True)
        models.load_published_feeds()
    except (OSError, yaml.YAMLError, ValueError) as exc:
        return [f"{models.REGISTRY_PATH.name}: {exc}"]
    errors = [f"invalid feed entry: {name}" for name in skipped]
    if not feeds:
        errors.append("no valid feeds")
    return errors


def main() -> int:
    errors = check(Path(sys.argv[1]) if len(sys.argv) > 1 else None)
    for error in errors:
        print(f"::error file=feeds.yaml::{error}" if "GITHUB_ACTIONS" in os.environ else error)
    if not errors:
        print("feeds.yaml OK")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
