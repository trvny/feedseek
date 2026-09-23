# AGENTS.md

- `feed_generators/`: Python generators and shared feed helpers.
- `feeds.yaml`: source registry.
- `feeds/`: tracked generated output; `cache/`: local generated state restored from R2, intentionally untracked.
- `site/`: static site and reader.
- `feeds-proxy/`: supporting Cloudflare Worker; stays in this repo.

## Project philosophy

- Feedseek improves RSS, Atom and JSON Feed as publishing protocols, not only as fallback for sites without feeds.
- Native feed is upstream source, not automatically final product. Reuse when reliable; normalize, enrich or repair when Feedseek can make output more complete, stable, expressive or interoperable.
- Prefer protocol-native semantics over ad-hoc payloads: durable entry identity, canonical links, truthful publication/update dates, useful metadata, provenance/categories, content/media and equivalent JSON Feed sidecars where supported.
- Preserve upstream meaning. Add fidelity and interoperability; do not invent editorial content or silently rewrite source facts.
- Hard quality contract stays universal and structural. Source-dependent richness (e.g. images, authors, categories, dates) is best-effort when upstream supports it.

## Repository conventions

- Check `main`, open PRs and recent changes before overlapping work.
- Prefer reliable native feed over scraping its HTML. Do not pass through unchanged when shared normalization or enrichment can improve published feed.
- Keep one maintained source of truth per concern; use shared normalization/deduplication helpers, not local copies.
- Fix maintained sources; regenerate `feeds/` / `cache/`, no hand-editing generated output. For incremental local generation, restore durable R2 cache immediately before each run.
- One broken source must not block unrelated feed updates.
- Failed or empty fetch must not replace last good feed with empty output.
- Secrets belong in provider/GitHub secret storage, never feeds, caches, logs or examples.
- `megalinter-reports/updated_sources` are suggestions: inspect diff; apply only intended fixes.

## Cloudflare

- Cloudflare Workers Builds deploys `feeds-proxy` from `feeds-proxy/`; GitHub Actions only checks it.
- Durable generation cache: private R2 bucket `feedseek-cache`, object `snapshots/cache.tar.gz`. Keep storage contract stable. Missing or unreadable durable state must fail closed; never auto-rebuild accumulator history from partial live-source refresh.
- `.github/workflows/deploy-cloudflare-pages.yml` is a dormant direct-upload fallback. No `feedseek` Pages project is currently provisioned, so using it requires an explicit Pages setup first.
- GitHub rename/transfer alone does not justify recreating KV/R2/D1 resources. After repo identity changes, verify Workers Builds Git connection; displayed slug alone proves neither survival nor breakage.
