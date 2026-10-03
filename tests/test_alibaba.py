import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))

import alibaba


class AlibabaTests(unittest.TestCase):
    def test_canonical_source_urls_strip_tracking_noise(self):
        self.assertEqual(
            [source.url for source in alibaba.SOURCES],
            [
                "https://www.alibabacloud.com/en/press-room/press-release",
                "https://www.alibabacloud.com/en/news/product",
                "https://www.alibabacloud.com/blog",
                "https://qwen.ai/research",
                "https://www.qwencloud.com/news",
            ],
        )

    def test_parses_press_release_detail_card(self):
        html = """
        <main>
          <article>
            <div>Sept 23 2026</div>
            <h3>Alibaba Cloud Expands Global Infrastructure</h3>
            <p>Global infrastructure and AI portfolio expansion.</p>
            <a href="/en/press-room/alibaba-cloud-expands-global-infrastructure-and-ai?_p_lc=1">View</a>
          </article>
        </main>
        """
        entries = alibaba.parse_source(html, alibaba.SOURCES[0])
        self.assertEqual(len(entries), 1)
        self.assertEqual(
            entries[0]["link"],
            "https://www.alibabacloud.com/en/press-room/alibaba-cloud-expands-global-infrastructure-and-ai",
        )
        self.assertEqual(entries[0]["date"].isoformat(), "2026-09-23T00:00:00+00:00")
        self.assertEqual(entries[0]["source"], "Alibaba Cloud Press")

    def test_product_update_gets_stable_synthetic_link(self):
        html = """
        <main>
          <div class="update-card">
            <h3>Cloud Governance Center is renamed</h3>
            <p>The English name changes to Agentic Cloud Governance Center.</p>
            <span>Jun 9,2026 / Cloud Governance Center (CGC)</span>
          </div>
        </main>
        """
        entries = alibaba.parse_source(html, alibaba.SOURCES[1])
        self.assertEqual(len(entries), 1)
        self.assertTrue(entries[0]["link"].startswith(
            "https://www.alibabacloud.com/en/news/product#product-2026-06-09-"
        ))

    def test_qwen_research_accepts_research_detail_links(self):
        html = """
        <main>
          <article>
            <h2>Qwen3.8-LiveTranslate: Names the speaker. Carries the meaning.</h2>
            <span>2026/09/18</span>
            <p>Simultaneous interpretation with lower lag.</p>
            <a href="/research/qwen3.8-livetranslate">Learn more</a>
          </article>
        </main>
        """
        entries = alibaba.parse_source(html, alibaba.SOURCES[3])
        self.assertEqual(len(entries), 1)
        self.assertEqual(
            entries[0]["link"],
            "https://qwen.ai/research/qwen3.8-livetranslate",
        )

    def test_product_rejects_unrelated_same_host_links(self):
        html = """
        <main>
          <article>
            <h3>Cloud Governance Center is renamed</h3>
            <span>Jun 9, 2026</span>
            <a href="/en/help">Unrelated site link</a>
          </article>
        </main>
        """
        entries = alibaba.parse_source(html, alibaba.SOURCES[1])

        self.assertEqual(len(entries), 1)
        self.assertTrue(entries[0]["link"].startswith(
            "https://www.alibabacloud.com/en/news/product#product-2026-06-09-"
        ))
        self.assertNotIn("/en/help", entries[0]["link"])

    def test_qwencloud_rejects_non_news_same_host_links(self):
        html = """
        <main>
          <article>
            <h2>Model Release on QwenCloud</h2>
            <time>2026-09-20</time>
            <a href="/models">Browse models</a>
          </article>
        </main>
        """
        entries = alibaba.parse_source(html, alibaba.SOURCES[4])

        self.assertEqual(len(entries), 1)
        self.assertTrue(entries[0]["link"].startswith(
            "https://www.qwencloud.com/news#qwencloud-2026-09-20-"
        ))
        self.assertNotIn("/models", entries[0]["link"])

    def test_explicit_publication_time_beats_date_mentioned_in_summary(self):
        html = """
        <main>
          <article>
            <h2>QwenCloud update</h2>
            <p>The preview mentions an event held on 2026-08-26.</p>
            <time datetime="2026-08-27">Aug 27, 2026</time>
          </article>
        </main>
        """
        entries = alibaba.parse_source(html, alibaba.SOURCES[4])

        self.assertEqual(len(entries), 1)
        self.assertEqual(
            entries[0]["date"].isoformat(),
            "2026-08-27T00:00:00+00:00",
        )

    def test_url_dedupe_keeps_same_title_from_distinct_sources(self):
        entries = [
            {
                "title": "Same announcement",
                "link": "https://www.alibabacloud.com/en/press-room/story",
                "date": None,
                "source": "Alibaba Cloud Press",
            },
            {
                "title": "Same announcement",
                "link": "https://www.alibabacloud.com/blog/story_1",
                "date": None,
                "source": "Alibaba Cloud Blog",
            },
        ]

        deduped = alibaba.dedupe_entries(
            entries,
            id_field="link",
            title_field=None,
            date_field="date",
        )
        self.assertEqual(len(deduped), 2)

    def test_qwencloud_news_can_fall_back_to_listing_fragment(self):
        html = """
        <main>
          <article>
            <strong>Model Release</strong>
            <h2>HappyOyster-1.0-Adventure on QwenCloud</h2>
            <p>An open-world model for real-time interaction.</p>
            <time>2026-09-20</time>
          </article>
        </main>
        """
        entries = alibaba.parse_source(html, alibaba.SOURCES[4])
        self.assertEqual(len(entries), 1)
        self.assertIn("#qwencloud-2026-09-20-", entries[0]["link"])


if __name__ == "__main__":
    unittest.main()
