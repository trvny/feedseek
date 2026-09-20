"""Pydantic models for feed configuration and settings."""

import logging
from pathlib import Path

import yaml
from pydantic import BaseModel, ValidationError, field_validator

logger = logging.getLogger(__name__)

REGISTRY_PATH = Path(__file__).parent.parent / "feeds.yaml"


class FeedConfig(BaseModel):
    """Configuration for a single feed generator."""

    script: str
    blog_url: str
    enabled: bool = True
    cache_required: bool = True
    cache_migrate_from: str | None = None

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
            name = item.get("name")
            title = item.get("title", "")
            if not isinstance(name, str) or not isinstance(title, str):
                raise ValueError(f"published_feeds entry {index} must use string name/title values")
            name, title = name.strip(), title.strip()
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
