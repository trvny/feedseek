"""Public APIs blog via native RSS."""

import argparse
import sys

from multi_rss import run

FEED_NAME = "apis"
BLOG_URL = "https://publicapis.dev/blog"
SOURCES = [("Public APIs", "https://publicapis.dev/feed.xml", 100)]


def main(full=False):
    return run(
        feed_name=FEED_NAME,
        title="APIs",
        subtitle="Public APIs blog: API design, development and discovery.",
        blog_url=BLOG_URL,
        author="Public APIs",
        sources=SOURCES,
        max_entries=100,
        dedupe_title_field=None,
        full=full,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate the APIs Atom feed")
    parser.add_argument("--full", action="store_true", help="Ignore cache and rebuild from scratch")
    sys.exit(0 if main(full=parser.parse_args().full) else 1)
