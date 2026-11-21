#!/usr/bin/env python3
"""Bounded WebSub notifications for selected Feedseek publication topics."""

from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import os
import sys
import time
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


def public_version_ready(topic: str, expected: str) -> bool:
    """Verify the unmodified public topic URL before notifying the hub."""
    if topic not in TOPICS or len(expected) != 64 or any(ch not in "0123456789abcdef" for ch in expected):
        raise ValueError("Invalid public WebSub topic or digest")
    for attempt in range(4):
        try:
            request = urllib.request.Request(topic, headers={
                "cache-control": "no-cache", "pragma": "no-cache",
                "user-agent": "Feedseek-WebSub/1.0",
            }, method="GET")
            # Fixed HTTPS canonical topic; responses bounded to 16 MiB.
            with urllib.request.urlopen(request, timeout=10) as response:  # nosec B310
                body = response.read(16 * 1024 * 1024 + 1)
                if response.status == 200 and len(body) <= 16 * 1024 * 1024 and entry_digest(body) == expected:
                    return True
        except (OSError, ValueError, ET.ParseError, http.client.HTTPException) as exc:
            print(f"WebSub public topic not ready: {topic}: {exc}", file=sys.stderr)
        if attempt < 3:
            time.sleep(3)
    return False


def publish(topics: list[str], expected: dict[str, str] | None = None) -> None:
    if not isinstance(topics, list) or any(topic not in TOPICS for topic in topics):
        raise ValueError("Unknown WebSub topic")
    expected = expected or {}
    failures = []
    for topic in sorted(set(topics)):
        try:
            if not public_version_ready(topic, expected.get(topic, "")):
                raise RuntimeError("Published topic content has not reached the canonical URL")
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
        except (OSError, RuntimeError, ValueError) as exc:
            failures.append(topic)
            print(f"WebSub publish skipped for {topic}: {exc}", file=sys.stderr)
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
        current = fingerprints()
        try:
            before = json.loads(args.path.read_text(encoding="utf-8"))
            if not isinstance(before, dict):
                raise ValueError("Invalid snapshot")
        except (OSError, ValueError):
            print("WebSub snapshot missing; skipping notifications", file=sys.stderr)
            before = current
        topics = changed_topics(before, current)
        expected = {PUBLIC_BASE + key + ".xml": digest for key, digest in current.items()
                    if PUBLIC_BASE + key + ".xml" in topics}
        with args.output.open("a", encoding="utf-8") as stream:
            stream.write("topics=" + json.dumps(topics, separators=(",", ":")) + "\n")
            stream.write("expected=" + json.dumps(expected, separators=(",", ":")) + "\n")
        print(f"WebSub changed topics: {len(topics)}")
    else:
        publish(
            json.loads(os.getenv("WEBSUB_TOPICS") or "[]"),
            json.loads(os.getenv("WEBSUB_EXPECTED") or "{}"),
        )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"WebSub: {exc}", file=sys.stderr)
        sys.exit(1)
