# WebSub publication pilot

Pilot topics: `jbzd.xml`, `memy.xml`, `rssboard.xml` on `https://rss.bartek.lol/`.

- Hub: `https://pubsubhubbub.appspot.com/` (third-party public WebSub hub).
- Publication contract: Atom `rel=self` and `rel=hub` links, or equivalent
  Atom-namespace links for RSS.
- Snapshot before generation; compare after refresh. Notify only changed pilot feeds.
- POST `hub.mode=publish` + `hub.url` after successful GitHub Pages deployment.
- Notification errors are nonfatal. Regular polling still works; Feedseek does
  not host a subscription service.
- Generated Pages XML includes discovery. Backend sources and historical URLs
  remain accessible.
- Feedseek stores no subscriber data or callbacks. The third-party hub verifies
  subscriptions and delivers updates.
- WebSub is not guaranteed instant delivery. Hub availability, subscriber
  verification, and reader support determine latency.

Tests: `uv run --locked python -m unittest tests/test_websub_publish.py`.

Notification delivery is best-effort. If publication is not yet visible at the
canonical URL, that cycle skips the push. A later entry change may retry.
Regular polling remains authoritative. No per-topic delivery ledger.
