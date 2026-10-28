# Feedseek Privacy Policy

_Last updated: October 28, 2026_

This policy applies to the public Feedseek service, including the Feedseek ChatGPT app and its MCP endpoint.

## What Feedseek processes

Feedseek is a read-only service for searching and retrieving publicly available RSS, Atom, JSON Feed, and related source content. The ChatGPT app may receive only the tool inputs needed to answer a request, such as search terms, a time cutoff, selected Feedseek source keys, result limits, or an opaque Feedseek result ID.

Feedseek does not require a user account, OAuth authorization, payment information, or credentials.

## Data collection and retention

Feedseek does not intentionally store ChatGPT conversation content, user prompts, per-user profiles, or tool arguments as persistent application data. It does not use cookies or build advertising profiles through the MCP app.

The service is hosted using third-party infrastructure, including Cloudflare and GitHub. Those providers may process ordinary network and request metadata needed to operate, secure, and deliver the service under their own policies.

The Reader panel keeps filters and selected public entries in memory. When the
ChatGPT host exposes widget-state APIs, it also saves filter values, selected
public entry IDs, titles, URLs, source names, compact summaries and uncertain-send
state through those APIs. The host may restore that state when the panel reopens;
closing the panel does not guarantee deletion of host-managed state. The panel
does not use browser storage or a Feedseek server-side user database.

Clicking **Use selection** shares selected entry details with the current ChatGPT
conversation through the host's model-context API. Where supported, the separate
**Send to chat** button sends the selected public details as a user-role message
after an explicit click. Host-managed widget state, messages and shared context
follow ChatGPT's retention rules.

## Public source content

Feedseek republishes or indexes public information from third-party feeds, APIs, and websites and links back to the original sources. Public source material may itself contain names, usernames, author information, or other information supplied by those sources. Feedseek does not control the privacy practices or accuracy of third-party publishers.

## Sharing and sale of data

Feedseek does not sell personal data. The app does not intentionally share user-specific ChatGPT data with feed publishers or advertisers. Requests may be processed by the infrastructure providers required to operate the service.

## Security

The ChatGPT app exposes read-only tools. It cannot create, modify, delete, send, publish, purchase, or otherwise change external state. Tool inputs are validated server-side, and retrieved feed content is treated as untrusted external content.

## Changes

This policy may be updated when Feedseek's functionality or infrastructure changes. Material changes will be reflected in this document and its update date.

## Contact

Feedseek is an open-source project maintained at https://github.com/trvny/feedseek. Questions about this policy can be raised through the repository or the maintainer's GitHub profile.
