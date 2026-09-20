import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))

import arxiv  # noqa: E402


class AlphaXivTests(unittest.TestCase):
    def test_parse_alphaxiv_extracts_paper_metadata(self):
        html = """
        <main>
          <div class="paper-card">
            <a href="/abs/2609.19969?ref=home">
              DeepSeek-V4.1-Flash: Pushing the Limits of KV Cache Compression
            </a>
            <div>DeepSeek-AI Anyi Xu</div>
            <p>
              Cross-layer cache reuse and low-precision storage reduce runtime
              and persistent KV-cache costs.
            </p>
            <span>17 Sept 2026</span>
            <span>69k views</span>
          </div>
        </main>
        """

        entries = arxiv.parse_alphaxiv(html)

        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(
            entry["link"], "https://www.alphaxiv.org/abs/2609.19969"
        )
        self.assertEqual(entry["source"], "alphaXiv Explore")
        self.assertEqual(entry["date"].date().isoformat(), "2026-09-17")
        self.assertIn("low-precision storage", entry["description"])

    def test_parse_alphaxiv_deduplicates_and_skips_known_papers(self):
        card = """
        <div>
          <a href="/abs/2609.11111">Paper A</a>
          <p>Summary</p>
          <span>18 Sept 2026</span>
        </div>
        """
        known = {"https://www.alphaxiv.org/abs/2609.11111"}

        self.assertEqual(arxiv.parse_alphaxiv(card + card, known), [])

    def test_parse_alphaxiv_ignores_non_paper_links(self):
        html = """
        <div>
          <a href="/researchers/yann-lecun">Yann LeCun</a>
          <span>17 Sept 2026</span>
        </div>
        """
        self.assertEqual(arxiv.parse_alphaxiv(html), [])

    def test_doc_sources_includes_alphaxiv(self):
        self.assertIn(
            ("alphaXiv Explore", "https://www.alphaxiv.org/"),
            arxiv.doc_sources(),
        )

    def test_main_wires_alphaxiv_as_best_effort_extra_source(self):
        with patch.object(arxiv, "run", return_value=True) as mocked_run:
            self.assertTrue(arxiv.main())

        kwargs = mocked_run.call_args.kwargs
        self.assertEqual(kwargs["feed_name"], "arxiv")
        self.assertEqual(kwargs["sources"], arxiv.SOURCES)
        self.assertEqual(kwargs["extra_scrapers"], (arxiv.collect_alphaxiv,))
        self.assertEqual(kwargs["max_entries"], 500)


if __name__ == "__main__":
    unittest.main()
