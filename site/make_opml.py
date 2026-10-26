#!/usr/bin/env python3
"""Generate subscriptions.opml from the published feed set.

Reuses build_site's feed discovery (feeds.yaml publication selection + live
titles parsed from each feed_*.xml) so the OPML always lists exactly what the
site publishes — no dead xmlUrls, custom title overrides carried through.

Writes only public/subscriptions.opml. The site builder also uses this
same build_opml() function, so publication has one source of truth:
feeds.yaml plus the generated feed XMLs. Feed Catcher's personal collection
is separate (site/feed-catcher.opml). Run as
``uv run --locked site/make_opml.py``.
"""
from __future__ import annotations

import sys
from pathlib import Path

SITE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SITE_DIR))
from build_site import build_opml, collect_feeds, site_base_url  # noqa: E402

OUT_DIR = SITE_DIR.parent / "public"


def main() -> None:
    feeds = collect_feeds()
    if not feeds:
        raise SystemExit("No feeds found — nothing to write into subscriptions.opml.")
    opml = build_opml(feeds, site_base_url())
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "subscriptions.opml").write_text(opml, encoding="utf-8")
    print(f"Wrote subscriptions.opml ({len(feeds)} feeds)")


if __name__ == "__main__":
    main()
