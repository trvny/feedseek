"""Alternate sitemap representations from the canonical URL list."""

import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

ATOM = "{http://www.w3.org/2005/Atom}"
SEARCH_VARIANTS = ("sitemap.txt", "sitemap-atom.xml", "sitemap-rss.xml")


def _xml(root):
    ET.indent(root)
    return ET.tostring(root, encoding="unicode", xml_declaration=True) + "\n"


def build_sitemap_variants(urls, base, updated=None):
    # Generated directory snapshot time, not a verified page modification date.
    updated = updated or datetime.now(timezone.utc).isoformat(timespec="seconds")
    if not urls or any(not url or not url.startswith(base) for url in urls):
        raise ValueError("Empty or foreign sitemap URL")

    atom = ET.Element("feed", xmlns=ATOM[1:-1])
    ET.SubElement(atom, "id").text = base + "sitemap-atom.xml"
    ET.SubElement(atom, "title").text = "Feedseek sitemap"
    ET.SubElement(ET.SubElement(atom, "author"), "name").text = "Feedseek"
    ET.SubElement(atom, "link", rel="self", href=base + "sitemap-atom.xml")
    ET.SubElement(atom, "link", href=base)
    ET.SubElement(atom, "updated").text = updated

    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "Feedseek sitemap"
    ET.SubElement(channel, "link").text = base
    ET.SubElement(channel, "description").text = "Canonical pages"

    for url in urls:
        entry = ET.SubElement(atom, "entry")
        ET.SubElement(entry, "id").text = url
        ET.SubElement(entry, "title").text = url
        ET.SubElement(entry, "link", href=url)
        ET.SubElement(entry, "updated").text = updated
        ET.SubElement(entry, "summary").text = url

        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = url
        ET.SubElement(item, "link").text = url
        ET.SubElement(item, "guid", isPermaLink="true").text = url

    return {
        "sitemap.txt": "\n".join(urls) + "\n",
        "sitemap.json": json.dumps([{"url": url} for url in urls], indent=2) + "\n",
        "sitemap-atom.xml": _xml(atom),
        "sitemap-rss.xml": _xml(rss),
    }
