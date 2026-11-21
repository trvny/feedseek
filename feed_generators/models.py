"""Pydantic models for feed configuration and settings."""

import json
import logging
from collections import Counter
import re
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit

import yaml
from pydantic import BaseModel, TypeAdapter, ValidationError, field_validator

logger = logging.getLogger(__name__)
BOOL = TypeAdapter(bool)

REGISTRY_PATH = Path(__file__).parent.parent / "feeds.yaml"
PUBLIC_STEM_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
RESERVED_PUBLIC_STEMS = frozenset({
    "index", "llms", "llms-full", "sitemap", "sitemap-atom",
    "sitemap-rss", "robots", "model-feeds", "subscriptions",
    "favicon", "site", "webmcp", "feedseek-search-index",
})


class FeedConfig(BaseModel):
    """Configuration for a single feed generator."""

    script: str
    blog_url: str
    enabled: bool = True
    cache_required: bool = True
    cache_migrate_from: str | None = None
    public_name: str | None = None

    @field_validator("script")
    @classmethod
    def script_must_exist(cls, v: str) -> str:
        script_path = Path(__file__).parent / v
        if not script_path.exists():
            msg = f"Script not found: {v}"
            raise ValueError(msg)
        return v


def load_feed_registry(return_skipped: bool = False):
    """Load and validate feeds.yaml.

    Invalid entries are logged and skipped rather than aborting the whole
    load, so one malformed config can never take down every other feed.

    Args:
        return_skipped: If True, return ``(feeds, skipped_names)`` instead of
            just ``feeds``. Defaults to False for backward compatibility.

    Returns:
        Dict mapping feed name to validated FeedConfig (valid entries only),
        or ``(dict, list[str])`` when ``return_skipped`` is True.

    Raises:
        FileNotFoundError: If feeds.yaml is missing.
    """
    if not REGISTRY_PATH.exists():
        msg = f"Feed registry not found: {REGISTRY_PATH}"
        raise FileNotFoundError(msg)

    with open(REGISTRY_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    feeds: dict[str, FeedConfig] = {}
    skipped: list[str] = []
    for name, config in data.get("feeds", {}).items():
        if not isinstance(config, dict):
            skipped.append(name)
            logger.error(
                "Skipping invalid feed config '%s' in feeds.yaml (expected mapping, got %s)",
                name,
                type(config).__name__,
            )
            continue

        try:
            feeds[name] = FeedConfig(**config)
        except ValidationError as e:
            skipped.append(name)
            errors = "; ".join(f"{'.'.join(str(p) for p in err['loc'])}: {err['msg']}" for err in e.errors())
            logger.error(
                "Skipping invalid feed config '%s' in feeds.yaml (%s)", name, errors
            )

    if skipped:
        logger.warning(
            "Loaded %d feed(s); skipped %d invalid: %s",
            len(feeds),
            len(skipped),
            ", ".join(skipped),
        )

    if return_skipped:
        return feeds, skipped
    return feeds


def load_active_publication_keys() -> set[str]:
    """Publication membership, including invalid-but-enabled cached sources.

    Generation validation owns config errors. Recovery may still serve the last
    good pair. Only explicit disable/removal withdraws a feed from publication.
    """
    with open(REGISTRY_PATH, encoding="utf-8") as source:
        data = yaml.safe_load(source) or {}
    entries = data.get("feeds") if isinstance(data, dict) else None
    if not isinstance(entries, dict):
        raise ValueError("feeds must be a mapping")
    def disabled(config: object) -> bool:
        if not isinstance(config, dict):
            return False  # Blank/broken config does not revoke old publication.
        try:
            return not BOOL.validate_python(config.get("enabled", True))
        except ValidationError:
            return False  # Bad config is not an explicit disable.

    return {
        name for name, config in entries.items()
        if isinstance(name, str) and not disabled(config)
    }


def load_published_feeds() -> list[tuple[str, str]] | None:
    """Load the ordered public feed selection from the canonical registry.

    A string entry publishes that feed with its generated title. A mapping may
    additionally provide ``title`` as a public-site override. Missing selection
    keeps the historical fallback of publishing every generated feed.
    """
    if not REGISTRY_PATH.exists():
        msg = f"Feed registry not found: {REGISTRY_PATH}"
        raise FileNotFoundError(msg)

    with open(REGISTRY_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    raw_selection = data.get("published_feeds")
    if raw_selection is None:
        return None
    if not isinstance(raw_selection, list):
        raise ValueError("published_feeds must be a list")

    known_feeds = set(data.get("feeds", {}))
    selection: list[tuple[str, str]] = []
    seen: set[str] = set()
    for index, item in enumerate(raw_selection, start=1):
        if isinstance(item, str):
            name, title = item.strip(), ""
        elif isinstance(item, dict):
            unknown = set(item) - {"name", "title"}
            if unknown:
                raise ValueError(f"published_feeds entry {index} has unknown fields: {sorted(unknown)}")
            raw_name = item.get("name")
            raw_title = item.get("title", "")
            if not isinstance(raw_name, str) or not isinstance(raw_title, str):
                raise ValueError(f"published_feeds entry {index} must use string name/title values")
            name, title = raw_name.strip(), raw_title.strip()
        else:
            raise ValueError(f"published_feeds entry {index} must be a string or mapping")

        if not name:
            raise ValueError(f"published_feeds entry {index} has an empty name")
        if name not in known_feeds:
            raise ValueError(f"published_feeds references unknown feed: {name}")
        if name in seen:
            raise ValueError(f"published_feeds contains duplicate feed: {name}")
        seen.add(name)
        selection.append((name, title))
    return selection

def validate_public_names(entries: dict) -> dict[str, str]:
    """Validate public names against all registry keys and reserved site files."""
    keys = set(entries)
    result: dict[str, str] = {}
    taken: set[str] = set()
    for key, config in entries.items():
        alias = config.get("public_name") if isinstance(config, dict) else None
        alias = key if alias is None else alias
        if not isinstance(alias, str) or not PUBLIC_STEM_RE.fullmatch(alias):
            raise ValueError(f"invalid public name for {key}: {alias!r}")
        if alias.startswith("feed_") or alias in RESERVED_PUBLIC_STEMS:
            raise ValueError(f"reserved public feed name: {alias}")
        if alias in keys and alias != key:
            raise ValueError(f"public name {alias} conflicts with a feed key")
        if alias in taken:
            raise ValueError(f"duplicate public name: {alias}")
        taken.add(alias)
        result[key] = alias
    return result


def runtime_public_names(entries: dict, previous_names: dict[str, str] | None = None) -> dict[str, str]:
    """Fallback only malformed or conflicting overrides; keep unrelated sources live."""
    keys = set(entries)
    candidates = {}
    for key, config in entries.items():
        override = config.get("public_name") if isinstance(config, dict) else None
        alias = key if override is None else override
        safe = (
            isinstance(alias, str)
            and PUBLIC_STEM_RE.fullmatch(alias) is not None
            and not alias.startswith("feed_")
            and alias not in RESERVED_PUBLIC_STEMS
            and (alias not in keys or alias == key)
        )
        if not safe:
            logger.warning("Ignoring unsafe public name for %s: %r", key, alias)
            alias = key
        candidates[key] = alias
    counts = Counter(candidates.values())
    previous_names = previous_names or {}
    for alias, count in counts.items():
        if count < 2:
            continue
        owners = [key for key, name in candidates.items() if name == alias]
        incumbent = next(
            (key for key in owners if previous_names.get(key) == alias),
            owners[0],
        )
        for key in owners:
            if key != incumbent:
                logger.warning("Ignoring conflicting public name for %s: %s", key, alias)
                candidates[key] = key
    return candidates


def _previous_public_names(entries: dict) -> dict[str, str]:
    """Reuse restored Model Feed URLs to prioritize an alias's current owner."""
    claims: dict[str, list[str]] = {}
    for key, config in entries.items():
        alias = config.get("public_name") if isinstance(config, dict) else None
        if isinstance(alias, str):
            claims.setdefault(alias, []).append(key)
    conflicting = {
        key for owners in claims.values() if len(owners) > 1 for key in owners
    }
    previous = {}
    for key in conflicting:
        if not PUBLIC_STEM_RE.fullmatch(key):
            continue
        path = REGISTRY_PATH.parent / "feeds" / f"feed_{key}.json"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(data, dict) or data.get("format") != "feedseek-model-feed":
            continue
        url = data.get("feed_url")
        if not isinstance(url, str):
            continue
        try:
            stem = Path(urlsplit(url).path).name
        except ValueError:
            continue
        if stem.endswith(".json"):
            previous[key] = stem[:-5]
    return previous


@lru_cache(maxsize=1)
def load_public_names() -> dict[str, str]:
    """One canonical mapping from stable keys to public file stems."""
    with open(REGISTRY_PATH, encoding="utf-8") as source:
        data = yaml.safe_load(source) or {}
    entries = data.get("feeds") if isinstance(data, dict) else None
    if not isinstance(entries, dict):
        raise ValueError("feeds must be a mapping")
    return runtime_public_names(entries, _previous_public_names(entries))


def public_feed_name(feed_name: str) -> str:
    return load_public_names().get(feed_name, feed_name)
