# AGENTS.md

## Cursor Cloud specific instructions

This repo is a **headless MCP server** (SEC EDGAR data). There is no GUI or web
UI — verify it with the terminal / MCP protocol, not a browser.

### Layout / how to run
- Python 3.12. Dependencies live in a venv at `.venv` (created by the update
  script). Run everything with `.venv/bin/python`.
- Entry point is `server.py`. Standard run commands are in `README.md`,
  `Procfile` (`web: python server.py`), and `railway.json`.
- Transport is chosen at startup by env vars (see `server.py` `__main__`):
  - `stdio` (default local, e.g. Cursor/Claude Desktop): `MCP_TRANSPORT=stdio`.
  - `sse` (web/Railway): set `MCP_TRANSPORT=sse` or `PORT`. Server listens on
    `0.0.0.0:$PORT` (default `8000`) and exposes the MCP stream at `/sse`.

### Required env var (gotcha)
- `EDGAR_USER_AGENT` is **mandatory** and must contain an `@` (name + email),
  or `EdgarClient()` raises at first tool call. SEC Fair Access rejects generic
  user agents with HTTP 403. This is a contact string, not an authenticated
  secret; any valid `Name email@domain` works. A gitignored `.env` with a
  placeholder is used for local dev; when running one-off commands, pass it
  inline, e.g. `EDGAR_USER_AGENT="Name you@example.com" .venv/bin/python server.py`.

### Network
- All tools (except pure parsing/unit tests) make **live** outbound calls to
  `data.sec.gov`, `www.sec.gov`, and `efts.sec.gov`. Outbound network is
  required for end-to-end tool tests; the client self-rate-limits to 8 req/s.

### Tests
- Unit tests are fully offline (no network): `.venv/bin/python -m unittest discover -s tests`.
