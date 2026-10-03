"""Normalize generated feed metadata after each generator run.

Besides fixing legacy raw-GitHub self links, keep Atom favicon metadata on one
stable Feedseek-hosted resolver. This post-generation pass is deliberately
independent of source fetch success: a failed generator must not leave stale
favicon metadata in the last-known-good XML/JSON pair.
"""

from __future__ import annotations

import html as html_lib
import json
import logging
import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from utils import (
    FAVICON_PROXY_ORIGIN,
    REPO_SLUG,
    favicon_proxy,
    large_icon,
    write_atomically,
)

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent
FEEDS_DIR = ROOT_DIR / "feeds"
CURRENT_PREFIX = f"https://raw.githubusercontent.com/{REPO_SLUG}/main/feeds/"
LEGACY_PREFIX = "https://raw.githubusercontent.com/trvny/feeds/main/feedseek/feeds/"
LEGACY_PREFIXES = (
    LEGACY_PREFIX,
    "https://raw.githubusercontent.com/trvny/feeds/main/feeds/",
    f"https://raw.githubusercontent.com/{REPO_SLUG}/main/feedseek/feeds/",
)

_TAG_RE = {
    tag: re.compile(rf"<{tag}>(?P<value>[^<]+)</{tag}>")
    for tag in ("icon", "logo")
}
_LINK_RE = re.compile(r"<link\b(?P<attrs>[^>]*)/?>", re.IGNORECASE)
_ATTR_RE = re.compile(
    r"""(?P<name>[:\w.-]+)\s*=\s*(?P<quote>["'])(?P<value>.*?)\2""",
    re.DOTALL,
)


def _tag_match(content: str, tag: str):
    return _TAG_RE[tag].search(content)


def _tag_indent(content: str, position: int) -> str:
    line_start = content.rfind("\n", 0, position) + 1
    prefix = content[line_start:position]
    return prefix if prefix.strip() == "" else ""


def _replace_tag(content: str, tag: str, value: str) -> str:
    escaped = html_lib.escape(value, quote=False)
    return _TAG_RE[tag].sub(
        lambda match: f"<{tag}>{escaped}</{tag}>",
        content,
        count=1,
    )


def _insert_after_tag(content: str, tag: str, new_tag: str, value: str) -> str:
    match = _tag_match(content, tag)
    if not match:
        return content
    indent = _tag_indent(content, match.start())
    escaped = html_lib.escape(value, quote=False)
    insertion = f"\n{indent}<{new_tag}>{escaped}</{new_tag}>"
    return content[: match.end()] + insertion + content[match.end() :]


def _atom_alternate_link(content: str) -> str:
    """Read the feed-level Atom alternate URL from generated local XML."""
    if "<feed" not in content:
        return ""
    header = content.split("<entry", 1)[0]
    for match in _LINK_RE.finditer(header):
        attrs = {
            attr.group("name").lower(): html_lib.unescape(attr.group("value")).strip()
            for attr in _ATTR_RE.finditer(match.group("attrs"))
        }
        if (attrs.get("rel") or "alternate") != "alternate":
            continue
        href = attrs.get("href", "")
        if href:
            return href
    return ""


def _source_domain(source_url: str) -> str:
    try:
        return (urlsplit(source_url).hostname or "").lower()
    except ValueError:
        return ""


def _managed_icon_options(icon_url: str, source_url: str) -> tuple[str | None, str]:
    """Preserve an explicit asset/provider while moving metadata behind Feedseek."""
    if not icon_url:
        return None, "google"

    if icon_url.startswith(FAVICON_PROXY_ORIGIN):
        query = parse_qs(urlsplit(icon_url).query)
        explicit_values = query.get("url")
        explicit: str | None = explicit_values[0] if explicit_values else None
        provider = (
            "duckduckgo"
            if (query.get("provider") or [""])[0] == "duckduckgo"
            else "google"
        )
        if explicit and not explicit.startswith("https://"):
            explicit = None
        return explicit, provider

    if "icons.duckduckgo.com/ip3/" in icon_url:
        return None, "duckduckgo"
    if "google.com/s2/favicons" in icon_url:
        return None, "google"

    try:
        source = urlsplit(source_url)
        root_guess = f"{source.scheme}://{source.netloc}/favicon.ico"
    except ValueError:
        root_guess = ""

    if icon_url.startswith("https://") and icon_url != root_guess:
        return icon_url, "google"
    return None, "google"


def _managed_icon_pair(content: str) -> tuple[str, str] | None:
    """Resolve Atom icon/logo values to the stable Feedseek favicon endpoint."""
    if "<feed" not in content:
        return None

    source_url = _atom_alternate_link(content)
    domain = _source_domain(source_url)
    if not domain:
        return None

    icon_match = _tag_match(content, "icon")
    logo_match = _tag_match(content, "logo")
    old_icon = html_lib.unescape(
        (icon_match or logo_match).group("value") if (icon_match or logo_match) else ""
    ).strip()
    explicit, provider = _managed_icon_options(old_icon, source_url)

    icon = favicon_proxy(
        domain,
        sz=64,
        provider=provider,
        url=explicit,
    )
    return icon, large_icon(icon, 256)


def _normalize_atom_icons(content: str) -> str:
    """Publish stable managed Atom icon/logo metadata for every source feed."""
    pair = _managed_icon_pair(content)
    if pair is None:
        return content
    icon_value, logo_value = pair

    icon = _tag_match(content, "icon")
    logo = _tag_match(content, "logo")

    if icon:
        content = _replace_tag(content, "icon", icon_value)
    elif logo:
        content = _insert_after_tag(content, "logo", "icon", icon_value)
    else:
        close = content.rfind("</feed>")
        if close < 0:
            return content
        content = (
            content[:close]
            + f"  <icon>{html_lib.escape(icon_value, quote=False)}</icon>\n"
            + content[close:]
        )

    logo = _tag_match(content, "logo")
    if logo:
        content = _replace_tag(content, "logo", logo_value)
    else:
        content = _insert_after_tag(content, "icon", "logo", logo_value)
    return content


def _rewrite_json_sidecar(xml_path: Path, icon: str, logo: str) -> None:
    """Update only JSON Feed icon metadata, preserving source-specific item cleanup."""
    sidecar = xml_path.with_suffix(".json")
    if not sidecar.exists():
        return

    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{sidecar.name} must contain a JSON object")
    payload["favicon"] = icon
    payload["icon"] = logo
    write_atomically(
        sidecar,
        lambda target: target.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        ),
    )


def normalize_feed_file(path: Path) -> bool:
    """Normalize self-link and favicon metadata in one generated feed pair."""
    content = path.read_text(encoding="utf-8")
    normalized = content
    for prefix in LEGACY_PREFIXES:
        if prefix != CURRENT_PREFIX:
            normalized = normalized.replace(prefix, CURRENT_PREFIX)
    normalized = _normalize_atom_icons(normalized)
    if normalized == content:
        return False

    sidecar = path.with_suffix(".json")
    previous_xml = path.read_bytes()
    previous_json = sidecar.read_bytes() if sidecar.exists() else None
    try:
        write_atomically(
            path,
            lambda target: target.write_text(normalized, encoding="utf-8"),
        )
        icon_pair = _managed_icon_pair(normalized)
        if icon_pair is not None:
            _rewrite_json_sidecar(path, *icon_pair)
    except Exception:
        write_atomically(path, lambda target: target.write_bytes(previous_xml))
        if previous_json is not None:
            write_atomically(sidecar, lambda target: target.write_bytes(previous_json))
        raise

    logger.info("Normalized feed metadata in %s", path.name)
    return True


def normalize_feed_self_links(feeds_dir: Path = FEEDS_DIR) -> list[Path]:
    """Normalize all generated XML feeds and return the files changed."""
    changed: list[Path] = []
    for path in sorted(feeds_dir.glob("feed_*.xml")):
        if normalize_feed_file(path):
            changed.append(path)
    return changed


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    try:
        changed = normalize_feed_self_links()
    except OSError as exc:
        logger.error("Could not normalize generated feed metadata: %s", exc)
        return 1
    logger.info("Normalized metadata in %d feed(s)", len(changed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
