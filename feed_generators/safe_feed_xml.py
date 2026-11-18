"""Shared XML boundary for generated/published feeds. DTDs forbidden."""

from io import BytesIO

from lxml import etree


class FeedXmlError(ValueError):
    """Invalid or disallowed feed XML."""


class _NoExternalResources(etree.Resolver):
    def resolve(self, url, public_id, context):
        raise FeedXmlError("external XML resources are not allowed")


def parse_feed_xml(source, *, strip_ignorable=True):
    parser = etree.XMLParser(
        resolve_entities=False,
        load_dtd=False,
        no_network=True,
        huge_tree=False,
        remove_comments=strip_ignorable,
        remove_pis=strip_ignorable,
    )
    parser.resolvers.add(_NoExternalResources())
    try:
        if isinstance(source, bytes):
            tree = etree.parse(BytesIO(source), parser)
        else:
            # Open local paths ourselves; never let libxml fetch a source URI.
            with open(source, "rb") as stream:
                tree = etree.parse(stream, parser)
    except etree.XMLSyntaxError as exc:
        raise FeedXmlError(str(exc)) from exc
    if tree.docinfo.doctype:
        raise FeedXmlError("XML document type declarations are not allowed")
    return tree
