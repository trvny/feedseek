# Everything runs through uv, the same way CI does. The old fallback to a bare
# `python` silently used whatever was on PATH, which cannot satisfy
# requires-python = ">=3.14" on most machines, so a missing uv surfaced as a
# confusing import or syntax error. Without the fallback it fails as itself.
# Deliberately not a $(error) guard: that is evaluated at parse time and would
# take `help` and `clean` down with it, and they need no interpreter.
PY := uv run --locked
RUN_FEED := $(PY) feed_generators/run_all_feeds.py --feed

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show available targets
	@grep -hE '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

.PHONY: install
install: ## Install the locked dependencies (fails if uv.lock is stale — run `make lock`)
	uv sync --locked

# --locked everywhere means the lock is never refreshed as a side effect of
# running something, which is what keeps local runs identical to CI. Changing
# pyproject.toml is therefore an explicit step.
.PHONY: lock
lock: ## Refresh uv.lock after editing pyproject.toml
	uv lock

.PHONY: feeds
feeds: ## Generate all feeds (incremental)
	$(PY) feed_generators/run_all_feeds.py

.PHONY: feeds-full
feeds-full: ## Regenerate all feeds from scratch (ignore cache)
	$(PY) feed_generators/run_all_feeds.py --full

.PHONY: feed
feed: ## Generate one feed: make feed NAME=<feeds.yaml name>
	@test -n "$(NAME)" || (echo "NAME is required; use a feeds.yaml name" >&2; exit 2)
	$(RUN_FEED) "$(NAME)"

.PHONY: feed-full
feed-full: ## Regenerate one feed from scratch: make feed-full NAME=<feeds.yaml name>
	@test -n "$(NAME)" || (echo "NAME is required; use a feeds.yaml name" >&2; exit 2)
	$(RUN_FEED) "$(NAME)" --full

# Compatibility for the historical `make feeds_<name>` shortcuts. Registry
# names now come from feeds.yaml instead of being duplicated as recipes here.
.PHONY: FORCE
FORCE:

feeds_%: FORCE
	$(RUN_FEED) "$*"

FULL_FEEDS := trojka czworka nexusmods_news jbzd foobar2000
FULL_TARGETS := $(addprefix feeds_,$(addsuffix _full,$(FULL_FEEDS)))
.PHONY: $(FULL_TARGETS)
$(FULL_TARGETS): feeds_%_full:
	$(RUN_FEED) "$*" --full

.PHONY: feeds_beatport
feeds_beatport: ## Compatibility alias for the Beatport Top 100 feed
	$(RUN_FEED) beatport_top100

.PHONY: feeds_windows11_release_notes
feeds_windows11_release_notes: ## Compatibility alias for Microsoft/Windows updates
	$(RUN_FEED) microsoft_updates

# Common Ninja is also consumed by the consolidated SaaS generator, but this
# standalone helper remains useful and is not a feeds.yaml entry.
.PHONY: feeds_commoninja
feeds_commoninja: ## Generate only the standalone Common Ninja blog feed
	$(PY) feed_generators/commoninja.py

.PHONY: validate
validate: ## Validate all generated feeds
	$(PY) feed_generators/validate_feeds.py

.PHONY: clean
clean: ## Remove generated feeds and cache
	rm -f feeds/feed_*.xml feeds/feed_*.json cache/*_posts.json