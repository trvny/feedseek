# Security Policy

## Reporting a vulnerability

Please report security issues privately through GitHub's **Report a vulnerability** flow for this repository instead of opening a public issue:

https://github.com/trvny/feedseek/security/advisories/new

Include enough detail to reproduce and assess the issue, such as the affected endpoint or workflow, expected and observed behavior, and a minimal proof of concept when practical.

Security reports are especially useful for issues involving the public feed proxy, SSRF or redirect validation, the MCP endpoint, workflow permissions or supply-chain controls, secret exposure, and unsafe parsing of untrusted feed content.

## Scope

A broken or changed upstream feed is normally a data-quality bug rather than a security vulnerability. Please use a regular GitHub issue for those reports unless the behavior creates a security boundary bypass.
