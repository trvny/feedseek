# Feedseek cache

Feedseek stores per-source incremental state in local `cache/`, intentionally
untracked. The durable source of truth is the private Cloudflare R2 object
`feedseek-cache/snapshots/cache.tar.gz`.

## Incremental generation

1. Restore the R2 snapshot immediately before each incremental run.
2. Validate archive paths, required per-feed cache files, JSON structures and
   the snapshot manifest.
3. Replace the local cache tree with the validated snapshot; never merge it
   with potentially stale local data.
4. Generate and validate feeds. Upload the new cache snapshot first.
5. Publish updated tracked `feeds/` artifacts only after a successful backup.

`make feeds`, `make feed NAME=...` and compatibility Make targets perform the
restore automatically. Direct incremental generators require the same one-shot
restore marker. Explicit full/stateless generation is separate from scheduled
production and must not overwrite the shared R2 accumulator snapshot.

The account needs `CLOUDFLARE_ACCOUNT_ID` and `CLOUDFLARE_API_TOKEN` with
Workers R2 Storage read/write permissions. The bucket and object must exist.
Missing credentials, missing or invalid durable state, incomplete manifests or
failed backup **fail closed** instead of publishing partial history.

`cache/.snapshot-manifest.json` records the complete durable cache set for
each successful backup. Restore checks that established state has not
silently disappeared. Required caches follow `feeds.yaml`; truly stateless
sources explicitly declare `cache_required: false`.

## Retention and size

`save_cache` retains up to `DEFAULT_CACHE_LIMIT` (2,000) dated entries per
feed by default. Combined feeds use fair per-source allocation rather than
letting high-volume sources displace quiet ones. Undated entries remain
separate from the dated quota; a feed needing deeper history can override the
limit or opt out with `limit=None`.

The upload hard limit `FEEDSEEK_CACHE_MAX_BYTES` defaults to 128 MB. Exceeding
it aborts publication; it never silently truncates the durable cache.

## Ownership

`feeds/` holds published artifacts in Git. R2 owns the mutable, incremental
cache. Do not hand-edit generated feeds, commit cache seeds or reconstruct an
accumulator from a partial live-source fetch. Historical migration statistics
are not part of the operating contract.
