import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))

import newsify


class NewsifyTests(unittest.TestCase):
    def test_requested_sources_are_registered(self):
        self.assertEqual(
            newsify.SOURCES,
            [
                (
                    "Newsify Polski",
                    "https://newsify.today/polish/PL",
                    "polish",
                    "pl",
                ),
                (
                    "Newsify English",
                    "https://newsify.today/english/PL",
                    "english",
                    "en",
                ),
            ],
        )

    def test_parses_polish_cards_and_deduplicates_repeated_article_links(self):
        html = """
        <main>
          <article>
            <img src="/images/story.webp" />
            <h3>Nowy ważny temat w Polsce</h3>
            <div>01.10.2026, 18:42</div>
            <p>Krótki opis artykułu, który powinien trafić do feedu.</p>
            <div>Trend: ważny temat</div>
            <a href="/polish/PL/article/wazny-temat/1234/nowy-wazny-temat-w-polsce">Czytaj więcej</a>
            <a href="/polish/PL/article/wazny-temat/1234/nowy-wazny-temat-w-polsce">Czytaj więcej</a>
          </article>
        </main>
        """
        entries = newsify.parse_listing(
            html,
            "Newsify Polski",
            "https://newsify.today/polish/PL",
            "polish",
            "pl",
        )

        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry["title"], "Nowy ważny temat w Polsce")
        self.assertEqual(
            entry["link"],
            "https://newsify.today/polish/PL/article/wazny-temat/1234/nowy-wazny-temat-w-polsce",
        )
        self.assertEqual(entry["date"].isoformat(), "2026-10-01T16:42:00+00:00")
        self.assertEqual(entry["source"], "Newsify Polski")
        self.assertEqual(entry["language"], "pl")
        self.assertEqual(entry["trend"], "ważny temat")
        self.assertIn("Krótki opis", entry["description"])
        self.assertEqual(entry["image"], "https://newsify.today/images/story.webp")

    def test_parses_english_card_and_uses_slug_when_link_text_is_generic(self):
        html = """
        <main>
          <div class="card">
            <span>15.01.2026, 09:15</span>
            <p>English summary for the Poland edition.</p>
            <a href="/english/PL/article/example/abcd/poland-launches-new-program">Read more</a>
          </div>
        </main>
        """
        entries = newsify.parse_listing(
            html,
            "Newsify English",
            "https://newsify.today/english/PL",
            "english",
            "en",
        )

        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry["title"], "Poland launches new program")
        self.assertEqual(entry["date"].isoformat(), "2026-01-15T08:15:00+00:00")
        self.assertEqual(entry["source"], "Newsify English")
        self.assertEqual(entry["language"], "en")
        self.assertIsNone(entry["trend"])

    def test_normalizes_repeatedly_escaped_article_paths(self):
        html = """
        <article>
          <div>01.10.2026, 18:42</div>
          <a href="/polish/PL/article/%252525C5%2525259Bwinouj%252525C5%2525259Bcie/id/%252525C5%2525259Bwinouj%252525C5%2525259Bcie">Czytaj więcej</a>
        </article>
        """
        entries = newsify.parse_listing(
            html,
            "Newsify Polski",
            "https://newsify.today/polish/PL",
            "polish",
            "pl",
        )
        self.assertEqual(
            entries[0]["link"],
            "https://newsify.today/polish/PL/article/%C5%9Bwinouj%C5%9Bcie/id/%C5%9Bwinouj%C5%9Bcie",
        )

    def test_ambiguous_warsaw_time_uses_shared_standard_time_semantics(self):
        self.assertEqual(
            newsify.parse_date("25.10.2026, 02:30").isoformat(),
            "2026-10-25T01:30:00+00:00",
        )

    def test_missing_timestamp_does_not_borrow_from_adjacent_card(self):
        html = """
        <main>
          <section>
            <div class="card">
              <h3>Pierwszy artykuł bez daty</h3>
              <p>Opis pierwszego artykułu.</p>
              <a href="/polish/PL/article/pierwszy/1/pierwszy-artykul">Czytaj więcej</a>
            </div>
            <div class="card">
              <img src="/images/second.webp" />
              <h3>Drugi artykuł</h3>
              <div>01.10.2026, 18:42</div>
              <p>Opis drugiego artykułu.</p>
              <a href="/polish/PL/article/drugi/2/drugi-artykul">Czytaj więcej</a>
            </div>
          </section>
        </main>
        """
        entries = newsify.parse_listing(
            html,
            "Newsify Polski",
            "https://newsify.today/polish/PL",
            "polish",
            "pl",
        )
        self.assertEqual(len(entries), 2)
        self.assertIsNone(entries[0]["date"])
        self.assertEqual(entries[0]["description"], "Opis pierwszego artykułu.")
        self.assertIsNone(entries[0]["image"])
        self.assertEqual(entries[1]["date"].isoformat(), "2026-10-01T16:42:00+00:00")

    def test_dedupe_keeps_distinct_urls_with_same_headline(self):
        entries = [
            {
                "title": "Ten sam tytuł",
                "link": "https://newsify.today/polish/PL/article/a/1/story",
                "date": None,
            },
            {
                "title": "Ten sam tytuł",
                "link": "https://newsify.today/polish/PL/article/b/2/story",
                "date": None,
            },
        ]
        self.assertEqual(len(newsify._dedupe_articles(entries)), 2)

    def test_ignores_non_article_links_and_external_hosts(self):
        html = """
        <main>
          <div>01.10.2026, 18:42</div>
          <a href="/polish/PL">Home</a>
          <a href="https://notnewsify.today/polish/PL/article/foo/1/bar">Lookalike host</a>
          <a href="https://example.com/polish/PL/article/foo/2/bar">External</a>
        </main>
        """
        entries = newsify.parse_listing(
            html,
            "Newsify Polski",
            "https://newsify.today/polish/PL",
            "polish",
            "pl",
        )
        self.assertEqual(entries, [])


if __name__ == "__main__":
    unittest.main()
