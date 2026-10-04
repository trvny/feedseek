"""GitHub ecosystem feed: GitHub's own blogs plus the app store built on top
of GitHub Releases.

All regular sources are native RSS:

  * The GitHub Blog and its per-topic channels (changelog, engineering,
    security, open source, AI/ML, enterprise). The channels are subsets of the
    main feed, so the cross-source URL/title dedupe in ``multi_rss`` collapses
    the overlap and the per-topic label survives on whichever copy is kept.
  * GitHub Status incident history.
  * Komi Store, an open-source app store that distributes GitHub Releases.
    Its feed is served from komistore.app but every link points at
    github-store.org, which is the same site under its older domain.
  * The wider Git/GitHub tooling ecosystem: Mergify, GitGuardian,
    GitKraken, Tower, Shields.io, git-annex, Jekyll, Travis CI and HelloGitHub.
  * Star History's blog (scraped index) and newsletter (native Beehiiv RSS).
    The newsletter is the requested rss.beehiiv.com/feeds/BbNzf9ozGZ.xml.
  * travnie organization activity via GitHub's public organization Events API.
    GitHub's private organization dashboard feed requires authentication and is
    deliberately not mirrored into this public Feedseek feed.
  * The GitHubTrendingRSS streams. Daily, weekly and monthly list the same
    repositories over different windows, so they share one source label: the
    URL dedupe collapses the overlap and the per-source quota treats trending
    as a single bucket instead of giving it three shares of the feed. Those
    items carry no per-item date; ``multi_rss`` stamps them on first sight.
  * Track Awesome List's full and weekly feeds. They share one source label so
    overlapping list updates are deduplicated and use one combined quota.

BeeWare News has no native feed used here, so the generator folds it in with
a small HTML adapter.

The changelog is the highest-volume channel by far, so it gets the largest
quota. The global cap keeps the combined feed bounded while per-source quotas
preserve space for lower-volume ecosystem sources.
"""

import argparse
import re
import sys
from urllib.parse import parse_qsl, quote, urlencode, urljoin, urlparse, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup
from multi_rss import get_html, logger, parse_date, run
from utils import sanitize_xml, stable_fallback_date

FEED_NAME = "github"

TRENDING = "GitHub Trending"
AWESOME_LISTS = "Track Awesome List"
MERGIFY_CHANGELOG_RSS_URL = "https://docs.mergify.com/changelog/rss.xml"
BEEWARE_NEWS_URL = "https://beeware.org/news/"
BEEWARE_LABEL = "BeeWare News"
BEEWARE_MAX = 20
_BEEWARE_ARTICLE_RE = re.compile(r"^/news/[^/]+/20\d{2}/[^/]+/?$")

STAR_HISTORY_URL = "https://www.star-history.com/"
STAR_HISTORY_BLOG_URL = "https://www.star-history.com/blog/"
STAR_HISTORY_BLOG_LABEL = "Star History Blog"
STAR_HISTORY_BLOG_MAX = 20
STAR_HISTORY_NEWSLETTER_LABEL = "Star History Newsletter"
STAR_HISTORY_NEWSLETTER_RSS_URL = "https://rss.beehiiv.com/feeds/BbNzf9ozGZ.xml"
_STAR_HISTORY_ARTICLE_RE = re.compile(r"^/blog/[^/?#]+/?$")

TRAVNIE_ORG = "travnie"
TRAVNIE_ACTIVITY_LABEL = "travnie GitHub Activity"
TRAVNIE_ACTIVITY_MAX = 80
TRAVNIE_PUBLIC_EVENTS_URL = (
    f"https://api.github.com/orgs/{TRAVNIE_ORG}/events?per_page=100"
)

SOURCES = [
    ("GitHub Changelog", "https://github.blog/changelog/feed/", 40),
    ("GitHub Engineering", "https://github.blog/engineering/feed/", 30),
    ("GitHub Security", "https://github.blog/security/feed/", 30),
    ("GitHub Open Source", "https://github.blog/open-source/feed/", 30),
    ("GitHub AI & ML", "https://github.blog/ai-and-ml/feed/", 30),
    ("GitHub Enterprise", "https://github.blog/enterprise-software/feed/", 20),
    ("GitHub Agentic Workflows", "https://github.github.com/gh-aw/blog/rss.xml", 20),
    ("GitHub Status", "https://www.githubstatus.com/history.atom", 25),
    ("Komi Store", "https://komistore.app/blog/feed.xml", 20),
    ("The GitHub Blog", "https://github.blog/feed/", 40),
    ("Mergify Changelog", MERGIFY_CHANGELOG_RSS_URL, 30),
    ("GitGuardian", "https://blog.gitguardian.com/rss/", 20),
    ("GitKraken", "https://www.gitkraken.com/feed", 15),
    ("Tower", "https://feeds.git-tower.com/tower-blog", 20),
    ("Shields.io", "https://shields.io/blog/atom.xml", 15),
    ("git-annex", "https://git-annex.branchable.com/news/index.atom", 15),
    ("Jekyll", "https://jekyllrb.com/feed.xml", 10),
    ("Travis CI", "https://www.travis-ci.com/feed/", 10),
    ("HelloGitHub", "https://hellogithub.com/rss", 20),
    (STAR_HISTORY_NEWSLETTER_LABEL, STAR_HISTORY_NEWSLETTER_RSS_URL, 15),
    (TRENDING, "https://mshibanami.github.io/GitHubTrendingRSS/daily/all.xml", 15),
    (TRENDING, "https://mshibanami.github.io/GitHubTrendingRSS/weekly/all.xml", 15),
    (TRENDING, "https://mshibanami.github.io/GitHubTrendingRSS/monthly/all.xml", 15),
    (AWESOME_LISTS, "https://www.trackawesomelist.com/rss.xml", 20),
    (AWESOME_LISTS, "https://www.trackawesomelist.com/week/rss.xml", 20),
]

PER_SOURCE_QUOTA = {
    "": 30,
    "GitHub Changelog": 60,
    "GitHub Status": 20,
    TRENDING: 20,
    AWESOME_LISTS: 30,
    STAR_HISTORY_BLOG_LABEL: 20,
    STAR_HISTORY_NEWSLETTER_LABEL: 15,
    TRAVNIE_ACTIVITY_LABEL: 40,
}


def _meta(page, attr, value):
    element = page.find("meta", attrs={attr: value})
    return element["content"].strip() if element and element.get("content") else None


def scrape_beeware_news(known_links):
    """Scrape BeeWare's news index and normalize new article pages."""
    index = get_html(BEEWARE_NEWS_URL)
    if not index:
        return []

    soup = BeautifulSoup(index, "html.parser")
    links = []
    seen = set()
    for anchor in soup.find_all("a", href=True):
        link = urljoin(BEEWARE_NEWS_URL, anchor["href"].split("#")[0].split("?")[0])
        parsed = urlparse(link)
        if parsed.hostname not in {"beeware.org", "www.beeware.org"}:
            continue
        if not _BEEWARE_ARTICLE_RE.match(parsed.path):
            continue
        canonical = f"https://beeware.org{parsed.path}"
        if canonical in seen or canonical in known_links:
            continue
        seen.add(canonical)
        links.append(canonical)

    entries = []
    for link in links:
        try:
            html = get_html(link)
            if not html:
                continue
            page = BeautifulSoup(html, "html.parser")
            title = _meta(page, "property", "og:title")
            if not title:
                heading = page.find("h1")
                title = heading.get_text(" ", strip=True) if heading else None
            if not title:
                continue

            description = (
                _meta(page, "property", "og:description")
                or _meta(page, "name", "description")
                or title
            )
            published = _meta(page, "property", "article:published_time")
            if not published:
                time_el = page.find("time", datetime=True)
                published = time_el.get("datetime") if time_el else None
            image = _meta(page, "property", "og:image")

            entries.append(
                {
                    "title": sanitize_xml(title),
                    "link": link,
                    "date": parse_date(published) if published else stable_fallback_date(link),
                    "description": sanitize_xml(description),
                    "source": BEEWARE_LABEL,
                    "image": image,
                }
            )
        except Exception:
            continue
        if len(entries) >= BEEWARE_MAX:
            break
    return entries


def _parse_star_history_blog(html, known_links=None):
    """Parse Star History's server-rendered blog index."""
    known_links = known_links or set()
    soup = BeautifulSoup(html, "html.parser")
    entries = []
    seen = set()
    for anchor in soup.select("a[href^='/blog/']"):
        href = anchor.get("href", "").split("#", 1)[0].split("?", 1)[0]
        if not _STAR_HISTORY_ARTICLE_RE.match(href):
            continue
        link = urljoin(STAR_HISTORY_URL, href)
        if link in known_links or link in seen:
            continue
        title_el = anchor.find(["h2", "h3"])
        if not title_el:
            continue
        title = sanitize_xml(title_el.get_text(" ", strip=True))
        if not title:
            continue
        date_el = anchor.find("time") or anchor.find("span")
        date_text = date_el.get_text(" ", strip=True) if date_el else ""
        seen.add(link)
        entries.append(
            {
                "title": title,
                "link": link,
                "date": parse_date(date_text) if date_text else stable_fallback_date(link),
                "description": title,
                "source": STAR_HISTORY_BLOG_LABEL,
            }
        )
        if len(entries) >= STAR_HISTORY_BLOG_MAX:
            break
    return entries


def scrape_star_history_blog(known_links):
    """Fetch Star History's blog index and normalize its newest posts."""
    html = get_html(STAR_HISTORY_BLOG_URL)
    if not html:
        return []
    return _parse_star_history_blog(html, known_links)



_EVENT_TITLE_ACTIONS = {
    "BranchProtectionRuleEvent": "updated branch protection in",
    "CheckRunEvent": "updated a check run in",
    "CheckSuiteEvent": "updated a check suite in",
    "CommitCommentEvent": "commented on a commit in",
    "DeleteEvent": "deleted a ref from",
    "DiscussionCommentEvent": "commented on a discussion in",
    "ForkEvent": "forked",
    "GollumEvent": "updated wiki pages in",
    "MemberEvent": "updated repository membership in",
    "MembershipEvent": "updated team membership in",
    "PublicEvent": "made public",
    "RepositoryEvent": "updated repository settings in",
    "SponsorshipEvent": "updated sponsorship in",
    "StatusEvent": "updated commit status in",
    "WatchEvent": "starred",
}


def _travnie_api_headers():
    """Build headers for GitHub's public organization Events API."""
    return {
        "Accept": "application/vnd.github+json",
        "User-Agent": "feedseek/github",
        "X-GitHub-Api-Version": "2026-03-10",
    }


def _fetch_travnie_events():
    """Fetch public travnie organization events without authentication."""
    try:
        response = requests.get(
            TRAVNIE_PUBLIC_EVENTS_URL,
            headers=_travnie_api_headers(),
            timeout=30,
        )
    except requests.RequestException as exc:
        logger.warning("travnie public events fetch failed: %s", exc)
        return []

    if response.status_code != 200:
        logger.warning(
            "travnie public events returned HTTP %s",
            response.status_code,
        )
        return []

    try:
        payload = response.json()
    except ValueError as exc:
        logger.warning("travnie public events returned invalid JSON: %s", exc)
        return []
    if isinstance(payload, list):
        return payload

    logger.warning("travnie public events returned an unexpected payload")
    return []


def _event_payload_url(event):
    """Prefer the page touched by an event over the repository homepage."""
    payload = event.get("payload") or {}
    if event.get("type") == "GollumEvent":
        pages = payload.get("pages")
        if isinstance(pages, list):
            for page in pages:
                if not isinstance(page, dict):
                    continue
                html_url = page.get("html_url")
                if (
                    isinstance(html_url, str)
                    and html_url.startswith("https://github.com/")
                ):
                    return html_url

    for key in (
        "comment",
        "review",
        "discussion",
        "pull_request",
        "issue",
        "release",
        "forkee",
    ):
        value = payload.get(key)
        if not isinstance(value, dict):
            continue
        html_url = value.get("html_url")
        if isinstance(html_url, str) and html_url.startswith("https://github.com/"):
            return html_url

    repo = event.get("repo") or {}
    repo_name = repo.get("name") if isinstance(repo, dict) else None
    if not isinstance(repo_name, str) or "/" not in repo_name:
        return ""

    base = f"https://github.com/{repo_name}"
    if event.get("type") == "PushEvent":
        head = payload.get("head")
        if isinstance(head, str) and re.fullmatch(r"[0-9a-fA-F]{7,40}", head):
            return f"{base}/commit/{head}"

    if event.get("type") == "CreateEvent":
        ref = payload.get("ref")
        ref_type = payload.get("ref_type")
        if (
            isinstance(ref, str)
            and ref
            and ref_type in {"tag", "branch"}
        ):
            return f"{base}/tree/{quote(ref, safe='')}"

    if event.get("type") == "GollumEvent":
        return f"{base}/wiki"

    return base


def _event_title(event):
    """Create a compact human title from a GitHub Events API object."""
    event_type = str(event.get("type") or "GitHubEvent")
    actor_obj = event.get("actor") or {}
    repo_obj = event.get("repo") or {}
    payload = event.get("payload") or {}

    actor = "Someone"
    if isinstance(actor_obj, dict):
        actor = (
            actor_obj.get("display_login")
            or actor_obj.get("login")
            or actor
        )
    repo = TRAVNIE_ORG
    if isinstance(repo_obj, dict):
        repo_name = repo_obj.get("name")
        if isinstance(repo_name, str) and repo_name:
            repo = repo_name

    if event_type == "PullRequestEvent":
        number = payload.get("number")
        action = payload.get("action") or "updated"
        return f"{actor} {action} PR #{number} in {repo}"

    if event_type in {"IssuesEvent", "IssueCommentEvent"}:
        issue = payload.get("issue") or {}
        number = issue.get("number") if isinstance(issue, dict) else None
        if event_type == "IssueCommentEvent":
            comment = payload.get("comment") or {}
            comment_id = comment.get("id") if isinstance(comment, dict) else None
            suffix = f" · comment {comment_id}" if comment_id else ""
            is_pull_request = (
                isinstance(issue, dict)
                and isinstance(issue.get("pull_request"), dict)
            )
            target = "PR" if is_pull_request else "issue"
            return f"{actor} commented on {target} #{number} in {repo}{suffix}"
        verb = payload.get("action") or "updated"
        return f"{actor} {verb} issue #{number} in {repo}"

    if event_type == "PullRequestReviewCommentEvent":
        pull_request = payload.get("pull_request") or {}
        number = (
            pull_request.get("number")
            if isinstance(pull_request, dict)
            else None
        )
        comment = payload.get("comment") or {}
        comment_id = comment.get("id") if isinstance(comment, dict) else None
        suffix = f" · comment {comment_id}" if comment_id else ""
        return f"{actor} commented on PR #{number} in {repo}{suffix}"

    if event_type == "PullRequestReviewEvent":
        pull_request = payload.get("pull_request") or {}
        number = (
            pull_request.get("number")
            if isinstance(pull_request, dict)
            else None
        )
        review = payload.get("review") or {}
        review_id = review.get("id") if isinstance(review, dict) else None
        suffix = f" {review_id}" if review_id else ""
        action = payload.get("action") or "created"
        return f"{actor} {action} review{suffix} on PR #{number} in {repo}"

    if event_type == "DiscussionEvent":
        action = payload.get("action") or "created"
        return f"{actor} {action} a discussion in {repo}"

    if event_type == "PushEvent":
        ref = str(payload.get("ref") or "").removeprefix("refs/heads/")
        head = payload.get("head")
        ref_suffix = f" ({ref})" if ref else ""
        head_suffix = (
            f" · {head[:7]}"
            if isinstance(head, str) and re.fullmatch(r"[0-9a-fA-F]{7,40}", head)
            else ""
        )
        return f"{actor} pushed to {repo}{ref_suffix}{head_suffix}"

    if event_type == "ReleaseEvent":
        release = payload.get("release") or {}
        tag = release.get("tag_name") if isinstance(release, dict) else None
        action = payload.get("action") or "published"
        suffix = f" {tag}" if tag else ""
        return f"{actor} {action} release{suffix} in {repo}"

    if event_type == "CreateEvent":
        ref_type = payload.get("ref_type") or "ref"
        ref = payload.get("ref")
        suffix = f" {ref}" if ref else ""
        return f"{actor} created {ref_type}{suffix} in {repo}"

    verb = _EVENT_TITLE_ACTIONS.get(event_type)
    if verb:
        return f"{actor} {verb} {repo}"

    event_name = re.sub(r"Event$", "", event_type)
    event_name = re.sub(r"(?<!^)(?=[A-Z])", " ", event_name).lower()
    return f"{actor} triggered {event_name} in {repo}"


def _event_identity_url(base_link, event_id):
    """Keep canonical anchors while giving every GitHub event a durable identity."""
    parsed = urlsplit(base_link)
    if parsed.fragment:
        query = parse_qsl(parsed.query, keep_blank_values=True)
        query.append(("feedseek_event", event_id))
        return urlunsplit(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                urlencode(query),
                parsed.fragment,
            )
        )
    return f"{base_link}#feedseek-event-{quote(event_id, safe='')}"


def _normalize_travnie_event(event):
    """Convert one GitHub Events API object into a Feedseek entry."""
    if not isinstance(event, dict):
        return None
    event_id = str(event.get("id") or "").strip()
    created_at = event.get("created_at")
    if not event_id or not isinstance(created_at, str):
        return None

    base_link = _event_payload_url(event)
    if not base_link:
        return None
    link = _event_identity_url(base_link, event_id)
    title = sanitize_xml(_event_title(event))
    return {
        "title": title,
        "link": link,
        "date": parse_date(created_at),
        "description": title,
        "source": TRAVNIE_ACTIVITY_LABEL,
    }


def scrape_travnie_activity(known_links):
    """Collect only public travnie activity from GitHub's tokenless API."""
    entries = []
    for event in _fetch_travnie_events():
        if event.get("public") is False:
            continue
        entry = _normalize_travnie_event(event)
        if not entry or entry["link"] in known_links:
            continue
        entries.append(entry)
        if len(entries) >= TRAVNIE_ACTIVITY_MAX:
            break
    return entries


EXTRA_SCRAPERS = (
    scrape_beeware_news,
    scrape_star_history_blog,
    scrape_travnie_activity,
)


def doc_sources():
    """Expose non-RSS sources to generated docs."""
    return [
        (BEEWARE_LABEL, BEEWARE_NEWS_URL),
        ("Star History", STAR_HISTORY_URL),
        (STAR_HISTORY_BLOG_LABEL, STAR_HISTORY_BLOG_URL),
        (TRAVNIE_ACTIVITY_LABEL, f"https://github.com/orgs/{TRAVNIE_ORG}"),
    ]


RETIRED_CACHE_SOURCES = {"Devin Desktop", "Devin Release Notes"}


def _active_cache_entry(entry):
    return entry.get("source") not in RETIRED_CACHE_SOURCES


def main(full=False):
    return run(
        feed_name=FEED_NAME,
        title="GitHub",
        subtitle="Combined GitHub feed: GitHub blogs and changelogs, GitHub "
        "Status, Mergify, BeeWare News, Star History, Komi Store, the Git "
        "tooling ecosystem, Track Awesome List, travnie organization activity "
        "and deduplicated GitHub trending streams.",
        blog_url="https://github.blog/",
        author="GitHub",
        sources=SOURCES,
        extra_scrapers=EXTRA_SCRAPERS,
        max_entries=400,
        per_source_cap=PER_SOURCE_QUOTA,
        cache_filter=_active_cache_entry,
        dedupe_title_field=None,
        full=full,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate the GitHub Atom feed")
    parser.add_argument(
        "--full", action="store_true", help="Ignore cache and rebuild from scratch"
    )
    sys.exit(0 if main(full=parser.parse_args().full) else 1)
