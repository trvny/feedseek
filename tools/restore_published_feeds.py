"""Restore the last published feed pairs from GitHub Pages into feeds/.

Pages is the only publication of generated output; feeds/ is no longer
tracked in Git. Generators need the previous pair as last-known-good state
(failed source keeps its old feed; unchanged feeds keep their dates), and
site builds need every pair. The Model Feed catalog lists every published
pair; any missing or invalid file fails closed so a partial restore never
reaches generation or a deploy.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urljoin

import requests
from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE = "https://trvny.github.io/feedseek/"
KEY_RE = re.compile(r"^[A-Za-z0-9_-]+$")
MAX_FILE_BYTES = 32 * 1024 * 1024
TIMEOUT_S = 30
USER_AGENT = "feedseek-restore/1.0 (+https://github.com/trvny/feedseek)"


class RestoreError(RuntimeError):
    """Published state could not be restored completely."""


def _get(session: requests.Session, url: str) -> bytes:
    response = session.get(url, timeout=TIMEOUT_S, headers={"User-Agent": USER_AGENT})
    if response.status_code != 200:
        raise RestoreError(f"GET {url} returned {response.status_code}")
    body = response.content
    if not body or len(body) > MAX_FILE_BYTES:
        raise RestoreError(f"GET {url} returned {len(body)} bytes")
    return body


def catalog_entries(catalog: object, base: str) -> list[tuple[str, str, str]]:
    """(key, xml_url, json_url) for every catalog row on the expected origin."""
    if not isinstance(catalog, dict) or catalog.get("format") != "feedseek-model-feed-catalog":
        raise RestoreError("unexpected Model Feed catalog format")
    rows = catalog.get("feeds")
    if not isinstance(rows, list) or not rows:
        raise RestoreError("Model Feed catalog lists no feeds")
    entries = []
    for row in rows:
        key = row.get("key") if isinstance(row, dict) else None
        xml_url, json_url = (row.get("feed_url"), row.get("model_feed_url")) if isinstance(row, dict) else (None, None)
        if not isinstance(key, str) or not KEY_RE.match(key):
            raise RestoreError(f"invalid catalog key: {key!r}")
        for url in (xml_url, json_url):
            if not isinstance(url, str) or not url.startswith(base):
                raise RestoreError(f"{key}: catalog URL outside {base}: {url!r}")
        entries.append((key, xml_url, json_url))
    return entries


def _check_pair(key: str, xml: bytes, model: bytes) -> None:
    try:
        etree.fromstring(xml, etree.XMLParser(resolve_entities=False, no_network=True))
    except etree.XMLSyntaxError as exc:
        raise RestoreError(f"{key}: invalid XML: {exc}") from exc
    try:
        payload = json.loads(model)
    except json.JSONDecodeError as exc:
        raise RestoreError(f"{key}: invalid JSON: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("format") != "feedseek-model-feed":
        raise RestoreError(f"{key}: not a Model Feed")


def restore(feeds_dir: Path, base: str = DEFAULT_BASE, workers: int = 8) -> int:
    """Download every published pair, then write all of them; returns pair count."""
    base = base.rstrip("/") + "/"
    with requests.Session() as session:
        catalog = json.loads(_get(session, urljoin(base, "model-feeds.json")))
        entries = catalog_entries(catalog, base)

        def fetch(entry: tuple[str, str, str]) -> tuple[str, bytes, bytes]:
            key, xml_url, json_url = entry
            xml, model = _get(session, xml_url), _get(session, json_url)
            _check_pair(key, xml, model)
            return key, xml, model

        with ThreadPoolExecutor(max_workers=workers) as pool:
            pairs = list(pool.map(fetch, entries))

    # Write only after every pair downloaded and parsed: all or nothing.
    feeds_dir.mkdir(parents=True, exist_ok=True)
    for key, xml, model in pairs:
        for suffix, data in ((".xml", xml), (".json", model)):
            target = feeds_dir / f"feed_{key}{suffix}"
            tmp = target.with_suffix(suffix + ".tmp")
            tmp.write_bytes(data)
            os.replace(tmp, target)
    return len(pairs)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--feeds-dir", type=Path, default=ROOT / "feeds")
    parser.add_argument("--base", default=os.getenv("FEEDSEEK_PUBLIC_BASE", DEFAULT_BASE))
    args = parser.parse_args()
    try:
        count = restore(args.feeds_dir, args.base)
    except (RestoreError, requests.RequestException, ValueError) as exc:
        print(f"Published feed restore failed: {exc}", file=sys.stderr)
        return 1
    print(f"Restored {count} published feed pairs into {args.feeds_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
