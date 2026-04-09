# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x     | ✅ Active  |

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Please report security issues by emailing the maintainer directly or opening a
[GitHub Security Advisory](https://github.com/m01126057061-lang/post-processing-ai-quality-api/security/advisories/new).

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

You will receive a response within **72 hours**. If confirmed, a patch will be
released within **7 days** for critical issues.

## Security Considerations

This API processes arbitrary text and invokes ML models. Key notes:

- **No authentication** is included by default — deploy behind an API gateway or
  add OAuth2/API-key middleware before exposing publicly.
- **Rate limiting** is built in (see `app/core/rate_limit.py`), but a reverse
  proxy (nginx, Caddy) is recommended for production.
- **Model outputs are not sanitised** — callers should sanitise before rendering
  in a browser context.
- **Audit log** (`data/quality_audit.db`) contains text previews — secure the
  file system path appropriately.
