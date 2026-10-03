import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "feed_generators"))

import daily_quote  # noqa: E402
import medium  # noqa: E402
import nasa  # noqa: E402
import usgov  # noqa: E402
import wykop  # noqa: E402
from utils import FAVICON_PROXY_ORIGIN  # noqa: E402


class FeedFaviconOverrideTests(unittest.TestCase):
    def test_medium_uses_representative_icon(self):
        with patch.object(medium, "run", return_value=True) as run:
            self.assertTrue(medium.main())

        icon = run.call_args.kwargs["icon"]
        self.assertTrue(icon.startswith(FAVICON_PROXY_ORIGIN))
        self.assertEqual(
            parse_qs(urlsplit(icon).query),
            {
                "domain": ["medium.com"],
                "sz": ["64"],
                "provider": ["duckduckgo"],
            },
        )

    def test_nasa_uses_representative_icon(self):
        with patch.object(nasa, "run", return_value=True) as run:
            self.assertTrue(nasa.main())

        icon = run.call_args.kwargs["icon"]
        self.assertTrue(icon.startswith(FAVICON_PROXY_ORIGIN))
        self.assertEqual(
            parse_qs(urlsplit(icon).query),
            {
                "domain": ["nasa.gov"],
                "sz": ["64"],
                "provider": ["duckduckgo"],
            },
        )

    def test_usgov_uses_representative_icon(self):
        with patch.object(usgov, "run", return_value=True) as run:
            self.assertTrue(usgov.main())

        self.assertEqual(run.call_args.kwargs["icon"], usgov.USAGOV_ICON)

    def test_daily_quote_uses_wikiquote_icon(self):
        xml = daily_quote.generate_atom_feed([]).atom_str().decode()

        self.assertIn(FAVICON_PROXY_ORIGIN, xml)
        self.assertIn("domain=en.wikiquote.org", xml)
        self.assertIn("provider=duckduckgo", xml)

    def test_wykop_uses_explicit_icon(self):
        xml = wykop.generate_atom_feed([]).atom_str().decode()

        self.assertIn(FAVICON_PROXY_ORIGIN, xml)
        self.assertIn("domain=wykop.pl", xml)
        self.assertIn("url=https%3A%2F%2Fwykop.pl%2Fstatic%2Fimg%2Ffavicons%2Ffavicon.png", xml)


if __name__ == "__main__":
    unittest.main()
