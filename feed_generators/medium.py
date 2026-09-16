"""Medium feed: combined Atom from Medium's native per-publication and
per-author RSS feeds — the Medium Blog, Medium Engineering, engineering and
design publications (Flutter, Angular, Android Developers, Google Cloud,
ProAndroidDev, Samsung Internet, Bootcamp, UX Planet), science and geopolitics
publications, AI/data publications, and a handful of individual authors.

Medium serves only the 10 newest items per feed, so history comes from the
JSON cache. The shared fair-share allocator gives every active source a turn;
we then hard-cap broad high-churn publications so they cannot consume leftover
slots when quieter engineering and author feeds run dry.

Angular is fetched twice on purpose: ``blog.angular.dev`` (the publication's
custom domain) and ``@angularteam`` (the profile) each carry a couple of posts
the other misses, and the normalized URL/title dedupe collapses the overlap.
"""

import argparse
import sys

from multi_rss import run
from utils import favicon_proxy

FEED_NAME = "medium"

# Medium caps every RSS endpoint at 10 items, so the fetch cap is just 10.
SOURCES = [
    ("The Medium Blog", "https://medium.com/feed/blog", 10),
    ("Medium Engineering", "https://medium.engineering/feed", 10),
    ("Medium Staff", "https://medium.com/feed/@MediumStaff", 10),
    ("Flutter", "https://medium.com/feed/flutter", 10),  # blog.flutter.dev/feed 404s
    ("Android Developers", "https://medium.com/feed/androiddevelopers", 10),
    ("Google Cloud", "https://medium.com/feed/google-cloud", 10),
    ("Artificial Intelligence in Plain English", "https://ai.plainenglish.io/feed", 10),
    ("David Rodenas PhD", "https://drpicox.medium.com/feed", 10),
    ("Towards AI", "https://pub.towardsai.net/feed", 10),
    ("AI Advances", "https://aiadvances.org/feed", 10),
    ("Data Science Collective", "https://medium.com/feed/data-science-collective", 10),
    ("Netflix TechBlog", "https://netflixtechblog.com/feed", 10),
    ("Netflix Technology Blog – Medium", "https://netflixtechblog.medium.com/feed", 10),
    ("Omio Engineering", "https://engineering.omio.com/feed", 10),
    ("Level Up Coding", "https://levelup.gitconnected.com/feed", 10),
    ("Skill Stuff", "https://medium.com/feed/skillstuff", 10),
    ("Stackademic", "https://blog.stackademic.com/feed", 10),
    ("Let’s Code Future", "https://medium.com/feed/lets-code-future", 10),
    ("Artificial Corner", "https://medium.com/feed/artificial-corner", 10),
    ("ProAndroidDev", "https://proandroiddev.com/feed", 10),
    ("Samsung Internet Developers", "https://medium.com/feed/samsung-internet-dev", 10),
    ("Yandex", "https://medium.com/feed/yandex", 10),
    ("Toyota Research Institute", "https://medium.com/feed/toyotaresearch", 10),
    ("Bootcamp", "https://medium.com/feed/design-bootcamp", 10),
    ("UX Planet", "https://uxplanet.org/feed", 10),
    ("The Useful Life", "https://medium.com/feed/the-useful-life", 10),
    ("The Riff", "https://medium.com/feed/the-riff", 10),
    ("Starts With A Bang!", "https://medium.com/feed/starts-with-a-bang", 10),
    ("Science Spectrum", "https://sciencespectrumu.com/feed", 10),
    ("Science Fiction", "https://medium.com/feed/science-fiction", 10),
    ("404: Geek Not Found", "https://medium.com/feed/404-geek-not-found", 10),
    ("The Ugly Monster", "https://medium.com/feed/theuglymonster", 10),
    ("The Geopolitics Report", "https://medium.com/feed/the-geopolitics-report", 10),
    ("The Geopolitical Economist", "https://medium.com/feed/the-geopolitical-economist", 10),
    ("Defence Affairs & Analysis", "https://medium.com/feed/@Defenceaffairs", 10),
    ("Russian Bear", "https://medium.com/feed/@russianbearussr", 10),
    ("Damien Walter", "https://damiengwalter.medium.com/feed", 10),
    ("Women in Technology", "https://medium.com/feed/womenintechnology", 10),
    ("The Code Frontier", "https://medium.com/feed/the-code-frontier", 10),
    ("Predict", "https://medium.com/feed/predict", 10),
    ("Philosophy Today", "https://medium.com/feed/philosophytoday", 10),
    ("The Knowledge of Laughter", "https://medium.com/feed/the-knowledge-of-laughter", 10),
    # Slug is the publication's old name; it now publishes as The Mixtape Memoirs.
    ("The Mixtape Memoirs", "https://medium.com/feed/three-imaginary-girls", 10),
    ("No Time", "https://medium.com/feed/no-time", 10),
    ("The Haven", "https://medium.com/feed/the-haven", 10),
    ("Globetrotters", "https://medium.com/feed/globetrotters", 10),
    ("Angular Blog", "https://blog.angular.dev/feed", 10),
    ("Angular (Medium)", "https://medium.com/feed/@angularteam", 10),
]

# A mapping is a hard ceiling in the shared allocator. Most sources may fill up
# to six slots when capacity remains; broad multi-author publications stop at
# four so an unusually busy outlet cannot backfill the aggregate by itself.
PER_SOURCE_CAPS = {
    "": 6,
    "Artificial Intelligence in Plain English": 4,
    "Towards AI": 4,
    "AI Advances": 4,
    "Predict": 4,
    "Data Science Collective": 4,
    "Level Up Coding": 4,
    "Skill Stuff": 4,
    "Stackademic": 4,
    "Let’s Code Future": 4,
    "Artificial Corner": 4,
}


def main(full=False):
    return run(
        feed_name=FEED_NAME,
        title="Medium",
        subtitle="Combined Medium feed: official and engineering publications, "
                 "AI and data-science outlets, science and geopolitics, design, "
                 "culture, and selected authors.",
        blog_url="https://medium.com/",
        author="Medium",
        sources=SOURCES,
        icon=favicon_proxy("medium.com", provider="duckduckgo"),
        max_entries=200,
        per_source_cap=PER_SOURCE_CAPS,
        full=full,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate the Medium Atom feed")
    parser.add_argument("--full", action="store_true", help="Ignore cache and rebuild from scratch")
    sys.exit(0 if main(full=parser.parse_args().full) else 1)
