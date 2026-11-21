"""Alternate sitemap representations from canonical page URLs."""

import html
import json
from datetime import datetime, timezone

SEARCH_VARIANTS = ("sitemap.txt", "sitemap-atom.xml", "sitemap-rss.xml")
XML_DECLARATION = '<?xml version="1.0" encoding="UTF-8"?>\n'


def build_sitemap_variants(
    urls: list[str], base: str, updated: str | None = None, *, id_base: str | None = None
) -> dict[str, str]:
    """Serialize URL maps without accepting or parsing XML input."""
    if not urls or any(not url or not url.startswith(base) for url in urls):
        raise ValueError("Empty or foreign sitemap URL")

    # Directory snapshot time; not a verified page modification date.
    stamp = html.escape(updated or datetime.now(timezone.utc).isoformat(timespec="seconds"))
    escaped_base = html.escape(base, quote=True)
    stable_base = id_base or base
    escaped_stable_base = html.escape(stable_base, quote=True)
    guid_permalink = "true" if stable_base == base else "false"
    atom_entries = []
    rss_items = []
    for canonical in urls:
        url = html.escape(canonical, quote=True)
        stable_id = html.escape(stable_base + canonical[len(base):], quote=True)
        atom_entries.append(
            f'  <entry><id>{stable_id}</id><title>{url}</title><link href="{url}"/>'
            f"<updated>{stamp}</updated><summary>{url}</summary></entry>"
        )
        rss_items.append(
            f"  <item><title>{url}</title><link>{url}</link>"
            f'<guid isPermaLink="{guid_permalink}">{stable_id}</guid></item>'
        )
    atom = "\n".join(atom_entries)
    rss = "\n".join(rss_items)
    return {
        "sitemap.txt": "\n".join(urls) + "\n",
        "sitemap.json": json.dumps([{"url": url} for url in urls], indent=2) + "\n",
        "sitemap-atom.xml": XML_DECLARATION + (
            '<feed xmlns="http://www.w3.org/2005/Atom">\n'
            f"  <id>{escaped_stable_base}sitemap-atom.xml</id>\n"
            "  <title>Feedseek sitemap</title>\n"
            "  <author><name>Feedseek</name></author>\n"
            f'  <link rel="self" href="{escaped_base}sitemap-atom.xml"/>\n'
            f'  <link href="{escaped_base}"/>\n'
            f"  <updated>{stamp}</updated>\n{atom}\n</feed>\n"
        ),
        "sitemap-rss.xml": XML_DECLARATION + (
            '<rss version="2.0"><channel>\n'
            "  <title>Feedseek sitemap</title>\n"
            f"  <link>{escaped_base}</link>\n"
            f"  <description>Canonical pages</description>\n{rss}\n"
            "</channel></rss>\n"
        ),
    }
