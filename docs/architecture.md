# Feedseek internals

Feedseek turns native feeds, public APIs and carefully selected web pages into stable, enriched RSS/Atom output plus one LLM-friendly Model Feed JSON file per XML feed. Native feeds are treated as upstream material rather than an automatic final form: the pipeline may normalize, repair or enrich them when that improves fidelity, stability or interoperability. The public README stays focused on using the project; implementation details live here.

## Pipeline

```text
feeds.yaml
   │
   ▼
fetch / parse / normalize / deduplicate
   │
   ├──▶ feeds/feed_<name>.xml + feed_<name>.json
   ├──▶ cache/                 last-known state
   └──▶ site/                  GitHub Pages + reader + generated model-feeds.json
             │
             ▼
     trvny.github.io/feedseek/
```

The defaults are intentionally conservative:

- prefer consuming a reliable native RSS/Atom feed over scraping HTML, while still normalizing or enriching the published output when useful;
- isolate source failures so one broken site does not block unrelated feeds;
- never replace the last good output with an empty result after a failed fetch;
- keep entry identity stable and hash-gate `updated` timestamps so unchanged items do not churn;
- deduplicate by normalized URL/title where sources overlap;
- keep generated `feeds/` and `cache/` data separate from maintained generator code.

## Feed quality contract

The publication gate has a small universal core. Every enabled feed must produce non-empty, parseable XML and one valid `feed_<name>.json` Model Feed with the same item count. Model Feed v1 requires unique non-empty IDs, non-empty plaintext and valid `text_kind` (`content`, `summary` or `title`); it preserves canonical links, dates, provenance-friendly authors/tags and optional imagery without reader-specific markup. JSON Feed 1.1 is used only as an internal projection, not an additional public artifact. Old `*.model.json` sidecars are no longer published.

The Pages build also emits `model-feeds.json`, a small catalog of public URLs, source metadata and per-feed timestamps derived from the same `feeds.yaml`-selected feed set. It contains **no copied articles** and is advertised in `llms.txt`, the HTML directory and the sitemap. Apps (including a future Sites dashboard) can read this static catalog, then fetch the original `feed_<name>.json` file directly without duplicating feed generation or adding a Cloudflare proxy.

The repository's [Model Feed index](model-feeds.md) covers every existing `feeds/feed_*.json`, including feeds outside the curated website selection. `feed_generators/model_feed.py` refreshes it after generating JSON sidecars; Update Feeds commits it with those artifacts. Regenerate the index alone with `uv run --locked feed_generators/docs_model_feeds.py`; add `--check` to detect drift.

Everything that depends on upstream richness stays adaptive. Images, authors, categories, provenance, summaries and publication/update dates should be preserved or enriched whenever the source gives enough evidence, but their absence alone does not fail a feed. A weather endpoint, a changelog and a newsroom should not be forced through the same editorial cookie cutter. When metadata is present, shared helpers should normalize it without inventing facts.

## Reader coverage

The browser Reader identifies entries by subscription feed URL and label plus Atom ID or RSS GUID, with a separate article-URL fallback when no ID is present. Distinct changelog versions, forecasts and observations may share one source-page URL and remain separate entries.

The browser Reader retains every usable, deduplicated entry returned by its subscriptions. Source filtering runs before display pagination: 250 entries per view, with **Show more** for the rest. The counter reports displayed and available entries. Responses above 16 MiB or 10,000 entries fail that feed's refresh, preserving its last loaded entries. Offline snapshots keep up to 5,000 recent entries and shrink further when browser storage is full; refresh reloads the feeds.

Browser WebMCP tools read the currently displayed page and share its source filter. The separate [remote MCP app](chatgpt/README.md) uses a recent index: up to 5,000 entries from 14 days, reserving up to five qualifying entries per source when capped. Neither MCP search nor its reader panel uses the browser Reader's pagination. Direct Model Feed JSON files contain the full published feed history, beyond the recent MCP index.

## Link and image enrichment

Before a generator writes its feed it can call `enrich_entries()` from `feed_generators/enrich.py`.

- **Links:** Google News wrapper URLs can be resolved to the real article URL while the wrapper remains the stable entry identity.
- **Images:** images already present in feed HTML are reused first; missing images can be filled from article Open Graph metadata.

Both paths are bounded and cache settled hits and misses, so repeated scheduled runs do not keep paying for the same lookup. The runtime knobs retained from the original README are:

- `FEEDSEEK_IMAGE_LOOKUPS=40` and `FEEDSEEK_GNEWS_LOOKUPS=40` cap lookups per feed/run;
- `FEEDSEEK_IMAGE_SECONDS=25` and `FEEDSEEK_GNEWS_SECONDS=25` cap time spent on each enrichment path;
- setting a lookup budget to `0` skips that enrichment path for the run.

## Local usage

Requires [uv](https://docs.astral.sh/uv/) or an equivalent Python environment using `pyproject.toml`.

```bash
make install        # install dependencies
make test           # run unit tests without regenerating feeds
make feeds          # generate all feeds incrementally
make feeds-full     # rebuild from scratch, ignoring the cache
make validate       # validate generated feeds
```

For the direct commands used by the repository checks:

```bash
uv sync --locked
make test
uv run --locked feed_generators/validate_feeds.py
```

In CI, feed `rel="self"` URLs are derived from `GITHUB_REPOSITORY`, so repository renames do not require hard-coded URL edits.

## Distribution boundary

The current `pyproject.toml` intentionally sets `[tool.uv] package = false`.
It manages an **application/repository workspace**, not an installable PyPI
distribution. Keeping `uv.lock` and `make test` reproducible benefits everyday
maintenance even if no external package is released.

Before making a distributable Python package, first ensure that its supported
entry points run from outside the repository checkout, with an explicit way to
find a caller-supplied `feeds.yaml` and output directory. Today
`feed_generators/models.py` resolves the registry relative to the checkout,
and site builders load code by adding `feed_generators/` to `sys.path`.
Packaging must not silently change scheduled behavior by moving those files.

Keep the existing ownership boundaries:

- `feed_generators/` plus its shared normalization and registry tools are
  candidates for a reusable **generator CLI/library**, once paths and resources
  are made portable and tested.
- `feeds.yaml` is the maintained source registry. Generated `feeds/`,
  `public/`, and local `cache/` are **runtime artifacts**, not wheel contents.
- `site/` is the GitHub Pages/reader publisher; `feeds-proxy/` is a separate
  Cloudflare Worker. Neither needs to be repackaged into the Python CLI.
- The private R2 snapshot is the authoritative incremental cache. A pip/uv
  installation must never rebuild or overwrite it automatically.

An independent packaging smoke test should eventually install the wheel in a
clean environment and invoke the supported CLI from another working directory,
using a temporary registry and destination. Until such a test exists, leave
`package = false` in place and treat publishing as a separate decision.

## Adding a feed

1. Create `feed_generators/<name>.py` exposing `main(full: bool)` and publish through the shared writer, which maintains the XML + single Model Feed JSON publication pair.
2. Register it in `feeds.yaml`.
3. Reuse shared HTTP, normalization, cache and feed helpers instead of creating local copies.
4. Add the source/feed row to the registry table in `README.md`; tests keep that table aligned with `feeds.yaml`.
5. Keep the source-count badges in all three language READMEs and the `registry-count` marker in `README_pl.md` aligned with `feeds.yaml`; tests enforce the current registry count.
6. Add it to `feeds.yaml` → `published_feeds` when it should appear on the public site.
7. Optionally add a per-feed Make target when a convenient dedicated or `*_full` command is useful.
8. Run the relevant tests and `make validate`.

`run_all_feeds.py` reads `feeds.yaml`, so the scheduled workflow discovers registered generators automatically.

## Repository layout

```text
.
├── .github/workflows/update-feeds.yml   # generate + validate + publish every 2 h
├── feeds.yaml                           # source registry
├── feed_generators/                     # maintained generators + shared helpers
├── feeds/                               # generated RSS/Atom + one Model Feed JSON per source
├── cache/                               # incremental state / last-known data
├── site/                                # GitHub Pages site and reader
├── feeds-proxy/                         # supporting Cloudflare Worker
├── tools/                               # manual diagnostics
└── docs/
    ├── architecture.md                  # this file
    ├── feeds.md                         # per-feed background and trade-offs
    ├── sources.md                       # generated source inventory
    └── cache.md                         # cache behavior and maintenance
```

For source-specific implementation notes see [feeds.md](feeds.md). For the generated source inventory see [sources.md](sources.md), and for cache details see [cache.md](cache.md).
