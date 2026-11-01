# Site and reader roadmap

Incremental work on the existing GitHub Pages site and reader. Preserve feed URLs,
entry identities, WebMCP behavior, and locally stored subscriptions and settings.

## Reader

- Make subscription edits transactional: Save applies additions, removals and
  settings; Cancel and closing the dialog discard pending changes. Preserve OPML
  import/export, existing overlays and recovery from failed refreshes.
- Fix settings layout overflow on narrow screens. Make feed management searchable.
- Add favorite sources and optional groups without changing subscriptions; keep
  existing source filtering and All available.
- Add article search, read/unread state and a local read-later list. Use stable
  feed identity plus entry ID; preserve distinct entries that share a URL.
- Investigate implausible upstream dates, including DJI ViewPoints. Preserve
  evidence, avoid inventing dates, and do not rewrite existing feed history by hand.
- Improve initial loading and stale/offline indicators; retain last good data on
  source failures. Measure cold/warm load and scrolling on an Android phone first.

## Catalog

- Add discoverable topic filters using one maintained source of metadata. Keep
  plain feed links, Model Feed catalog, subscriptions and search indexing intact.
- Clarify feed update time versus latest entry publication time and source failure.

## Architecture experiments

- Consider Astro components for the catalog incrementally, retaining the existing
  generated feed registry and static GitHub Pages deployment as sources of truth.
- Consider Preact for isolated interactive reader components when complexity
  justifies it; no reader rewrite or parallel implementation.
- Evaluate IndexedDB for snapshots and reading state with a migration that keeps
  existing preferences, subscriptions and cached data, including quota failures.
- Benchmark before adding list virtualization. Evaluate Workbox only with explicit
  freshness, cache eviction, update and offline recovery behavior.
