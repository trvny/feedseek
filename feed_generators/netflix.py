"""Netflix feed: official news plus independent release and catalog coverage."""

import argparse
import sys

from multi_rss import run

FEED_NAME = "netflix"
OFFICIAL = "official"

SOURCES = [
    ("Netflix Newsroom", "https://about.netflix.com/feed.xml", 40),
    ("Netflix Newsroom PL", "https://about.netflix.com/pl/feed.xml", 40),
    ("Netflix Life", "https://netflixlife.com/feed/", 40),
    ("New on Netflix", "https://news.newonnetflix.info/feed/", 40),
    ("New on Netflix US", "https://usa.newonnetflix.info/feed/", 40),
    ("New on Netflix UK", "https://uk.newonnetflix.info/feed/", 40),
    ("What's on Netflix", "https://www.whats-on-netflix.com/feed/", 40),
]


def main(full=False):
    return run(
        feed_name=FEED_NAME,
        title="Netflix",
        subtitle=(
            "Netflix announcements plus independent news, release, and catalog coverage."
        ),
        blog_url="https://about.netflix.com/",
        author="Feedseek",
        sources=SOURCES,
        source_tags={
            "Netflix Newsroom": OFFICIAL,
            "Netflix Newsroom PL": OFFICIAL,
        },
        max_entries=250,
        per_source_cap=50,
        full=full,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate the Netflix Atom feed")
    parser.add_argument("--full", action="store_true", help="Ignore cache and rebuild from scratch")
    sys.exit(0 if main(full=parser.parse_args().full) else 1)
