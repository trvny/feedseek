#!/usr/bin/env python3
"""Bounded WebSub notifications for selected Feedseek publication topics."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "feed_generators"))
from websub_config import HUB_URL as HUB, PUBLIC_BASE, PILOT_KEYS  # noqa: E402

FEEDS = ROOT / "feeds"
KEYS = tuple(sorted(PILOT_KEYS))
TOPICS = {PUBLIC_BASE + key + ".xml" for key in KEYS}
ATOM = "{http://www.w3.org/2005/Atom}"


def entry_digest(payload: bytes) -> str:
    """Hash the published entry content, ignoring volatile channel clocks/hub links."""
    root = ET.fromstring(payload)
    if root.tag == ATOM + "feed":
        items = root.findall(ATOM + "entry")
    elif root.tag == "rss":
        channel = root.find("channel")
        if channel is None:
            raise ValueError("Missing RSS channel")
        items = channel.findall("item")
    else:
        raise ValueError("Unexpected feed format")
    digest = hashlib.sha256()
    for entry in items:
        canonical = ET.canonicalize(
            ET.tostring(entry, encoding="unicode"), strip_text=True
        ).encode("utf-8")
        digest.update(len(canonical).to_bytes(4, "big"))
        digest.update(canonical)
    return digest.hexdigest()


def fingerprints(feeds_dir: Path = FEEDS) -> dict[str, str]:
    return {
        key: entry_digest((feeds_dir / f"feed_{key}.xml").read_bytes())
        for key in KEYS
        if (feeds_dir / f"feed_{key}.xml").is_file()
    }


def changed_topics(previous: dict[str, str], current: dict[str, str]) -> list[str]:
    return [
        PUBLIC_BASE + key + ".xml"
        for key in KEYS
        if key in current and previous.get(key) != current[key]
    ]


def publish(topics: list[str]) -> None:
    if not isinstance(topics, list) or any(topic not in TOPICS for topic in topics):
        raise ValueError("Unknown WebSub topic")
    failures = []
    for topic in sorted(set(topics)):
        try:
            body = urllib.parse.urlencode({"hub.mode": "publish", "hub.url": topic}).encode()
            request = urllib.request.Request(
                HUB, data=body,
                headers={"content-type": "application/x-www-form-urlencoded", "user-agent": "Feedseek-WebSub/1.0"},
                method="POST",
            )
            # Fixed HTTPS hub + allowlisted topic URLs; no arbitrary scheme or host.
            with urllib.request.urlopen(request, timeout=10) as response:  # nosec B310
                if response.status not in (200, 202, 204):
                    raise RuntimeError(f"WebSub hub responded {response.status}")
            print(f"WebSub publish accepted: {topic}")
        except (OSError, RuntimeError) as exc:
            failures.append(topic)
            print(f"WebSub publish failed for {topic}: {exc}", file=sys.stderr)
    if failures:
        raise RuntimeError(f"{len(failures)} of {len(topics)} WebSub topics failed")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["snapshot", "diff", "publish"])
    parser.add_argument("path", nargs="?", type=Path)
    parser.add_argument("output", nargs="?", type=Path)
    args = parser.parse_args()
    if args.operation == "snapshot":
        if args.path is None:
            parser.error("snapshot requires an output path")
        args.path.write_text(json.dumps(fingerprints()), encoding="utf-8")
    elif args.operation == "diff":
        if args.path is None or args.output is None:
            parser.error("diff requires snapshot and GITHUB_OUTPUT paths")
        before = json.loads(args.path.read_text(encoding="utf-8"))
        if not isinstance(before, dict):
            raise ValueError("Invalid snapshot")
        topics = changed_topics(before, fingerprints())
        with args.output.open("a", encoding="utf-8") as stream:
            stream.write("topics=" + json.dumps(topics, separators=(",", ":")) + "\n")
        print(f"WebSub changed topics: {len(topics)}")
    else:
        publish(json.loads(os.getenv("WEBSUB_TOPICS", "[]")))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"WebSub: {exc}", file=sys.stderr)
        sys.exit(1)
