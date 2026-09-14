"""Restore Feedseek's durable generation cache from Cloudflare R2."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

from restore_cache_archive import _cache_state, restore_cache_archive

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUCKET = "feedseek-cache"
DEFAULT_KEY = "snapshots/cache.tar.gz"
CACHE_MARKER = ".r2-restored"
_MISSING_PATTERNS = (
    "nosuchkey",
    "specified key does not exist",
    "object not found",
)


def is_missing_object_error(message: str) -> bool:
    text = message.casefold()
    return any(pattern in text for pattern in _MISSING_PATTERNS)


def _wrangler_path() -> Path:
    suffix = ".cmd" if os.name == "nt" else ""
    path = ROOT / "feeds-proxy" / "node_modules" / ".bin" / f"wrangler{suffix}"
    if not path.exists():
        raise FileNotFoundError(
            "locked Wrangler is not installed; run `npm --prefix feeds-proxy ci` first"
        )
    return path


def _fetch_archive(bucket: str, key: str, archive: Path) -> bool:
    if not os.environ.get("CLOUDFLARE_API_TOKEN") or not os.environ.get(
        "CLOUDFLARE_ACCOUNT_ID"
    ):
        raise RuntimeError("Cloudflare credentials are required for R2 cache restore")

    result = subprocess.run(
        [
            str(_wrangler_path()),
            "r2",
            "object",
            "get",
            f"{bucket}/{key}",
            "--file",
            str(archive),
            "--remote",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        return True

    detail = "\n".join(part for part in (result.stdout, result.stderr) if part).strip()
    if is_missing_object_error(detail):
        return False
    raise RuntimeError(detail or f"Wrangler exited with status {result.returncode}")


def required_cache_files(registry_path: Path = ROOT / "feeds.yaml") -> set[str]:
    """Return cache files required by enabled registry entries."""
    data = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
    required: set[str] = set()
    for name, config in data.get("feeds", {}).items():
        if not isinstance(config, dict) or not config.get("enabled", True):
            continue
        if config.get("cache_required", True):
            required.add(f"{name}_posts.json")
    return required


def validate_cache_snapshot(cache_dir: Path, required: set[str]) -> None:
    """Reject incomplete or malformed durable cache snapshots."""
    missing = sorted(name for name in required if not (cache_dir / name).is_file())
    if missing:
        raise ValueError("missing required cache file(s): " + ", ".join(missing))

    invalid = sorted(
        path.name
        for path in cache_dir.glob("*_posts.json")
        if not _cache_state(path)[0]
    )
    if invalid:
        raise ValueError("invalid cache JSON file(s): " + ", ".join(invalid))


def replace_cache_tree(restored: Path, target: Path) -> None:
    """Replace local cache state with the validated R2 snapshot."""
    stage = target.with_name(target.name + ".r2-stage")
    backup = target.with_name(target.name + ".r2-backup")
    shutil.rmtree(stage, ignore_errors=True)
    shutil.rmtree(backup, ignore_errors=True)
    shutil.copytree(restored, stage)
    if target.exists():
        target.rename(backup)
    try:
        stage.rename(target)
    except Exception:
        if backup.exists() and not target.exists():
            backup.rename(target)
        raise
    shutil.rmtree(backup, ignore_errors=True)


def restore_from_r2(bucket: str, key: str, target: Path) -> bool:
    target.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        archive = tmp_path / "cache.tar.gz"
        if not _fetch_archive(bucket, key, archive):
            return False
        restored = restore_cache_archive(archive, tmp_path / "restored")
        validate_cache_snapshot(restored, required_cache_files())
        replace_cache_tree(restored, target)

    (target / CACHE_MARKER).write_text("restored\n", encoding="utf-8")
    print("Replaced local cache with the authoritative R2 snapshot.")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket", default=DEFAULT_BUCKET)
    parser.add_argument("--key", default=DEFAULT_KEY)
    parser.add_argument("--merge-into", type=Path, default=ROOT / "cache")
    args = parser.parse_args()

    try:
        restored = restore_from_r2(args.bucket, args.key, args.merge_into)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"R2 cache restore failed: {exc}", file=sys.stderr)
        return 1

    if not restored:
        print(
            f"R2 object {args.bucket}/{args.key} does not exist yet.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
