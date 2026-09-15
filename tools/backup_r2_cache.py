"""Create and upload Feedseek's durable cache snapshot to Cloudflare R2."""

from __future__ import annotations

import argparse
import gzip
import os
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

from restore_r2_cache import (
    CACHE_MARKER,
    DEFAULT_BUCKET,
    DEFAULT_KEY,
    ROOT,
    _wrangler_path,
    required_cache_files,
    write_cache_manifest,
)

DEFAULT_MAX_BYTES = 128 * 1024 * 1024


def _normalized_info(path: Path, arcname: str) -> tarfile.TarInfo:
    info = tarfile.TarInfo(arcname)
    info.size = path.stat().st_size
    info.mode = 0o644
    info.uid = info.gid = 0
    info.uname = info.gname = ""
    info.mtime = 0
    return info


def create_cache_archive(
    cache_dir: Path,
    archive: Path,
    required: set[str],
    *,
    max_bytes: int,
) -> int:
    """Validate cache state and write a deterministic gzip tar snapshot."""
    write_cache_manifest(cache_dir, required)
    files = sorted(path for path in cache_dir.rglob("*") if path.is_file() and path.name != CACHE_MARKER)
    total = sum(path.stat().st_size for path in files)
    if total > max_bytes:
        raise ValueError(f"cache size limit exceeded: {total} > {max_bytes}")

    archive.parent.mkdir(parents=True, exist_ok=True)
    with archive.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as zipped:
            with tarfile.open(fileobj=zipped, mode="w") as bundle:
                root_info = tarfile.TarInfo("cache")
                root_info.type = tarfile.DIRTYPE
                root_info.mode = 0o755
                root_info.uid = root_info.gid = 0
                root_info.mtime = 0
                bundle.addfile(root_info)
                for path in files:
                    arcname = f"cache/{path.relative_to(cache_dir).as_posix()}"
                    info = _normalized_info(path, arcname)
                    with path.open("rb") as source:
                        bundle.addfile(info, source)
    return total


def upload_archive(bucket: str, key: str, archive: Path) -> None:
    if not os.environ.get("CLOUDFLARE_API_TOKEN") or not os.environ.get("CLOUDFLARE_ACCOUNT_ID"):
        raise RuntimeError("Cloudflare credentials are required for R2 cache backup")

    result = subprocess.run(
        [
            str(_wrangler_path()),
            "r2",
            "object",
            "put",
            f"{bucket}/{key}",
            "--file",
            str(archive),
            "--content-type",
            "application/gzip",
            "--remote",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = "\n".join(part for part in (result.stdout, result.stderr) if part).strip()
        raise RuntimeError(detail or f"Wrangler exited with status {result.returncode}")


def backup_to_r2(bucket: str, key: str, cache_dir: Path, max_bytes: int) -> int:
    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / "feedseek-cache.tar.gz"
        total = create_cache_archive(cache_dir, archive, required_cache_files(), max_bytes=max_bytes)
        upload_archive(bucket, key, archive)
    return total


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket", default=os.getenv("FEEDSEEK_CACHE_BUCKET", DEFAULT_BUCKET))
    parser.add_argument("--key", default=os.getenv("FEEDSEEK_CACHE_KEY", DEFAULT_KEY))
    parser.add_argument("--cache-dir", type=Path, default=ROOT / "cache")
    parser.add_argument(
        "--max-bytes",
        type=int,
        default=int(os.getenv("FEEDSEEK_CACHE_MAX_BYTES", DEFAULT_MAX_BYTES)),
    )
    args = parser.parse_args()
    try:
        total = backup_to_r2(args.bucket, args.key, args.cache_dir, args.max_bytes)
    except (OSError, RuntimeError, ValueError, tarfile.TarError) as exc:
        print(f"R2 cache backup failed: {exc}", file=sys.stderr)
        return 1
    print(f"Uploaded {total} bytes of durable cache state to R2.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
