# WebSub publication pilot

Pilot topics: `jbzd.xml`, `memy.xml`, `rssboard.xml` on `https://rss.bartek.lol/`.

- Hub: `https://pubsubhubbub.appspot.com/` (third-party public WebSub hub).
- Publication contract: Atom `rel=self` and `rel=hub` links, or equivalent Atom-namespace links for RSS.
- Snapshot before generation; compare after refresh. Notify only changed pilot feeds.
- POST `hub.mode=publish` + `hub.url` after successful GitHub Pages deployment.
- Notification errors are nonfatal. Regular polling still works, no subscription service hosted by Feedseek.
- Generated Pages XML includes discovery, while backend sources and historical URLs remain accessible.
- No per-user subscriptions or callback URLs stored by Feedseek. The third-party hub handles subscriber verification/delivery.
- WebSub isn't universal instant delivery: hub availability, subscriber verification and reader support determine end-to-end behavior.

Tests: `uv run --locked python -m unittest tests/test_websub_publish.py`.

Notification delivery is best-effort: if publication is not visible at the canonical URL within the bounded verification window, that cycle skips the push. A future entry change may trigger another attempt; normal feed polling remains authoritative. The pilot does not persist a per-topic delivery ledger.
