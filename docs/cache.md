# Feedseek cache

Feedseek keeps per-source JSON state in local `cache/`. The directory is
intentionally untracked; the durable source of truth is the private Cloudflare
R2 object `feedseek-cache/snapshots/cache.tar.gz`.

Incremental generation is fail-closed:

1. Restore the R2 snapshot immediately before each incremental run.
2. Validate archive safety, required per-feed cache files, and JSON structure.
3. Replace the local cache tree with that validated snapshot rather than merging
   it with possibly stale local state.
4. Generate and validate feeds, then upload the resulting cache snapshot.
5. Publish tracked feed updates only after the R2 upload succeeds.

`CLOUDFLARE_API_TOKEN` needs Workers R2 Storage read/write access for the account
in `CLOUDFLARE_ACCOUNT_ID`. The bucket and snapshot must already exist. Missing
credentials, bucket/object, malformed JSON, an incomplete snapshot, or a failed
backup stop the run without publishing feed changes.

Each successful backup also writes `cache/.snapshot-manifest.json`. The manifest
records the complete durable cache set from that run. Restore validates that set
before replacement, so a newly added feed can create its first cache while a
previously established cache cannot silently disappear from R2.

`make feeds`, `make feed NAME=...`, and the compatibility Make targets restore
R2 automatically. Direct incremental generator execution is guarded by the
same one-shot restore marker. Explicit full rebuilds are cache-independent, but
the scheduled production workflow intentionally uses the durable R2 state. The
standalone make feeds_commoninja helper is intentionally full/stateless and
never rewrites the shared R2 snapshot.

## Size is bounded by an entry limit

Nothing capped cache growth until 2026-08-08. Every entry ever seen was kept:
4chan reached **21 109 entries (7.9 MB) to publish a 200-entry feed**, and pap
held entries back to April 2021. The directory was 49.9 MB across 91 files and
82 335 entries, growing every two hours.

`save_cache` now keeps the newest `DEFAULT_CACHE_LIMIT` (2000) entries per feed
and drops the oldest.

**Recency alone would not have been safe.** Six of the seven caches this trims
belong to combined feeds whose sources are wildly unequal — tvp held 4345 TVP
Sport and 4167 TVP Info entries against 131 Moto, 65 Rozrywka, 53 Kultura and 39
Informacje. A plain newest-2000 slice is ~97% Sport and Info, and the quiet
sources disappear from the dedup state altogether: exactly what
`multi_rss.apply_per_source_cap` prevents in the published feed. `trim_entries`
mirrors that algorithm — newest-first, each source may fill an even share, and
once every source has hit that share or run dry, a second pass refills the
remaining slots *again round-robin*. Backfilling those leftovers by recency is
the obvious-looking design and was the original one; it leaked badly, because
the most prolific source then ate every slot the quiet ones could not fill.
See `allocate_fair_share` in `feed_generators/utils.py` for the numbers that
retired it. On the real tvp cache all
four quiet sources survive intact while Sport and Info drop to ~850 each. A
single-source cache gets a quota equal to the limit and so behaves like a plain
recency trim.

Dateless entries are split out and always kept rather than displacing recent
items (`sort_posts_for_feed` parks them after the dated ones, so a tail slice
would otherwise prefer them). The result can exceed `limit` by their count,
normally zero because `invoke_generator.freeze_missing_dates` fills them first.

2000 is deliberately generous. Every accumulator feed is far below it (the
largest, `beatport_top100`, holds 200), so none of them lose published history.
It trims 7 of 91 caches. Pass `limit=` to `save_cache` for a feed that needs a
deeper dedup window, or `limit=None` to opt out entirely.

This also protects the backup. If the cache exceeds
`FEEDSEEK_CACHE_MAX_BYTES` (128 MB), the upload step now fails and feed changes
are not published. The durable snapshot and tracked feeds therefore cannot drift
apart silently.

## Why untracking is now safe

`cache/` used to be committed because several generators accumulate history that
cannot be reconstructed from the current upstream page. Removing it without a
replacement could collapse a multi-entry feed to only the currently visible
items.

The R2 migration addresses the old blockers directly:

1. Incremental runs restore authoritative durable state before generators read
   cache files. Missing or invalid state fails closed.
2. The common cache loader and the two legacy list-cache loaders reject direct
   incremental execution without a fresh one-shot restore marker.
3. Feed artifact validation no longer uses repository cache presence to decide
   whether an enabled feed is established.
4. The restore contract derives required cache files from `feeds.yaml`. Stateful
   feeds are required by default; genuinely stateless entries declare
   `cache_required: false`.

The repository therefore keeps the publishable `feeds/` artifacts in Git while
R2 owns mutable generation state. Reintroducing a repository cache seed would
create two competing sources of truth and should be avoided.
