"""Public GitHub milestones for trvny and travnie, without commit-level noise.

Uses GitHub Events API for the owner user and organization. Intentionally skips
pushes, reviews, comments, stars and routine ref changes. Only public events in
repositories owned by trvny/travnie are published; no token or private data.
The API exposes at most 30 days of activity, so cached entries carry history.
"""
import argparse
import re
import sys
from urllib.parse import quote, urlsplit

import requests
from bs4 import BeautifulSoup
from multi_rss import logger, parse_date, run
from utils import sanitize_xml

FEED_NAME = "github_personal"
USER = "trvny"
ORG = "travnie"
USER_EVENTS_URL = f"https://api.github.com/users/{USER}/events/public"
ORG_EVENTS_URL = f"https://api.github.com/orgs/{ORG}/events"
EVENT_SOURCES = (("User", USER_EVENTS_URL), ("Organization", ORG_EVENTS_URL))
MAX_PAGES = 3
PAGE_SIZE = 100
MAX_EVENTS = 140
_ALLOWED_OWNERS = {USER, ORG}
_ALLOWED_PR_ACTIONS = {"opened", "reopened"}
_ALLOWED_ISSUE_ACTIONS = {"opened", "reopened", "closed"}


def _headers():
    return {
        "Accept": "application/vnd.github+json",
        "User-Agent": "feedseek/github-personal",
        "X-GitHub-Api-Version": "2026-03-10",
    }


def _fetch_events(endpoint):
    events = []
    for page in range(1, MAX_PAGES + 1):
        try:
            response = requests.get(
                endpoint,
                params={"per_page": PAGE_SIZE, "page": page},
                headers=_headers(),
                timeout=14,
            )
            if response.status_code != 200:
                logger.warning("GitHub events %s: HTTP %s", endpoint, response.status_code)
                break
            batch = response.json()
            if not isinstance(batch, list):
                logger.warning("GitHub events %s: unexpected payload", endpoint)
                break
            events.extend(batch)
            if len(batch) < PAGE_SIZE:
                break
        except (requests.RequestException, ValueError) as exc:
            logger.warning("GitHub events %s failed: %s", endpoint, exc)
            break
    return events


def _excerpt(text, limit=520):
    if not isinstance(text, str) or not text.strip():
        return ""
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = BeautifulSoup(text, "html.parser").get_text(" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()
    return sanitize_xml(text[:limit].rstrip())


def _github_url(value):
    if not isinstance(value, str):
        return ""
    parts = urlsplit(value)
    return value if parts.scheme == "https" and parts.hostname == "github.com" else ""


def _avatar(event):
    actor = event.get("actor") or {}
    value = actor.get("avatar_url") if isinstance(actor, dict) else None
    if not isinstance(value, str):
        return None
    parts = urlsplit(value)
    return value if parts.scheme == "https" and parts.hostname == "avatars.githubusercontent.com" else None


def _event_details(event):
    """Return kind, action, detail, URL and optional body for milestone events."""
    kind = event.get("type")
    payload = event.get("payload") or {}
    if not isinstance(payload, dict):
        return None
    action = payload.get("action")
    repo = event["repo"]["name"]
    base = f"https://github.com/{repo}"

    if kind == "PullRequestEvent":
        pr = payload.get("pull_request") or {}
        if not isinstance(pr, dict):
            return None
        merged = action == "closed" and pr.get("merged") is True
        if not merged and action not in _ALLOWED_PR_ACTIONS:
            return None
        action = "merged" if merged else action
        number = pr.get("number") or payload.get("number")
        title = pr.get("title") or f"PR #{number}"
        link = _github_url(pr.get("html_url")) or f"{base}/pull/{number}"
        return "Pull request", action, f"PR #{number} · {title}", link, pr.get("body")

    if kind == "IssuesEvent":
        issue = payload.get("issue") or {}
        if not isinstance(issue, dict) or issue.get("pull_request"):
            return None
        if action not in _ALLOWED_ISSUE_ACTIONS:
            return None
        number = issue.get("number")
        title = issue.get("title") or f"Issue #{number}"
        link = _github_url(issue.get("html_url")) or f"{base}/issues/{number}"
        return "Issue", action, f"#{number} · {title}", link, issue.get("body")

    if kind == "ReleaseEvent" and action == "published":
        release = payload.get("release") or {}
        if not isinstance(release, dict) or release.get("draft"):
            return None
        tag = release.get("tag_name") or ""
        title = release.get("name") or tag or "New release"
        link = _github_url(release.get("html_url")) or f"{base}/releases"
        return "Release", "published", f"{title} · {tag}" if tag and tag != title else title, link, release.get("body")

    if kind == "DiscussionEvent" and action == "created":
        discussion = payload.get("discussion") or {}
        if not isinstance(discussion, dict):
            return None
        title = discussion.get("title") or "New discussion"
        link = _github_url(discussion.get("html_url"))
        if not link:
            return None
        return "Discussion", "created", title, link, discussion.get("body")

    if kind == "CreateEvent" and payload.get("ref_type") == "repository":
        return "Repository", "created", repo, base, None

    if kind == "PublicEvent":
        return "Repository", "made public", repo, base, None

    return None


def normalize_event(event, stream):
    if not isinstance(event, dict) or event.get("public") is False:
        return None
    event_id = str(event.get("id") or "").strip()
    repo_obj = event.get("repo") or {}
    actor_obj = event.get("actor") or {}
    repo = repo_obj.get("name") if isinstance(repo_obj, dict) else None
    actor = actor_obj.get("login") if isinstance(actor_obj, dict) else None
    if not event_id or not isinstance(repo, str) or not isinstance(actor, str):
        return None
    owner, sep, _ = repo.partition("/")
    if not sep or owner.lower() not in _ALLOWED_OWNERS:
        return None
    if stream == "Organization" and owner.lower() != ORG:
        return None
    if stream == "User" and actor.lower() != USER:
        return None

    date = parse_date(event.get("created_at"))
    if not date:
        return None
    details = _event_details(event)
    if not details:
        return None
    kind, action, subject, link, body = details
    if not _github_url(link):
        return None

    # Event id preserves distinct open/merge milestones on the same pull request.
    canonical = f"{link}#feedseek-event-{quote(event_id, safe='')}"
    body_excerpt = _excerpt(body)
    description = f"{actor} · {repo} · {kind} {action}"
    if body_excerpt:
        description += f"\n{body_excerpt}"
    return {
        "title": sanitize_xml(f"{kind} {action}: {subject} [{repo}]"),
        "link": canonical,
        "date": date,
        "description": sanitize_xml(description),
        "source": f"{kind} {action}",
        "author": actor,
        "categories": [kind, action, repo],
        "image": _avatar(event),
    }


def scrape_activity(known_links):
    entries, seen = [], set()
    for stream, endpoint in EVENT_SOURCES:
        for event in _fetch_events(endpoint):
            entry = normalize_event(event, stream)
            if not entry or entry["link"] in known_links or entry["link"] in seen:
                continue
            seen.add(entry["link"])
            entries.append(entry)
    entries.sort(key=lambda item: item["date"], reverse=True)
    return entries[:MAX_EVENTS]


def doc_sources():
    return [
        ("trvny public activity", USER_EVENTS_URL),
        ("travnie public activity", ORG_EVENTS_URL),
    ]


def main(full=False):
    return run(
        feed_name=FEED_NAME,
        title="trvny + travnie · GitHub",
        subtitle="Public milestones: opened and merged PRs, issues, releases, discussions and repositories. No individual commits or routine comments.",
        blog_url="https://github.com/trvny",
        author="trvny & travnie",
        extra_scrapers=[scrape_activity],
        max_entries=240,
        per_source_cap={"": 65},
        dedupe_title_field=None,
        full=full,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate personal GitHub milestones")
    parser.add_argument("--full", action="store_true")
    sys.exit(0 if main(full=parser.parse_args().full) else 1)
