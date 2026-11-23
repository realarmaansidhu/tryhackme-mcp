# Contributing

Thanks for helping! A few ground rules keep this project safe to install.

## Setup

```bash
uv sync --extra dev
uv run pytest -q
npx @modelcontextprotocol/inspector uv run tryhackme-mcp   # poke at tools interactively
```

## Adding a tool

1. Find the endpoint: open the relevant page on tryhackme.com, DevTools → Network → filter `api/v2`.
2. Add the call in `src/tryhackme_mcp/server.py`:
   - `@tool()` for anything that only reads.
   - `@write_tool()` (or `@write_tool(destructive=True)`) for anything that changes an account. These
     only register when `THM_ALLOW_WRITES=1`, and every write goes through `THMClient.post`, which
     attaches the CSRF token the way the website does.
3. Render the result in `formatting.py`. Keep output short Markdown, and never pass through
   personal fields (email, phone, tokens). Whitelist; don't blacklist.
4. Add a mocked test in `tests/` (see existing ones; everything uses respx, nothing hits the network).
5. Add a row to the README tool table and `docs/API.md`.

## Not accepted

- Anything that bypasses bot protection, CAPTCHAs or rate limits.
- Bulk scraping or exporting premium content to share.
- Tools that fetch, guess or brute-force answers.
- Committed cookies, tokens or real account data, including in test fixtures.

## Releasing (maintainers)

Bump the version in `pyproject.toml`, `src/tryhackme_mcp/__init__.py`, `server.json` (both
places) and `manifest.json`, update `CHANGELOG.md`, then:

```bash
git tag v0.1.1 && git push --tags
```

The release workflow tests, publishes to PyPI, attaches the `.mcpb` bundle to a GitHub Release
and updates the MCP Registry entry.
