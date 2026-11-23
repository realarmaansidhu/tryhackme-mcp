# TryHackMe MCP Server

<!-- mcp-name: io.github.realarmaansidhu/tryhackme-mcp -->

[![tests](https://github.com/realarmaansidhu/tryhackme-mcp/actions/workflows/tests.yml/badge.svg)](https://github.com/realarmaansidhu/tryhackme-mcp/actions/workflows/tests.yml)
[![PyPI](https://img.shields.io/pypi/v/tryhackme-mcp)](https://pypi.org/project/tryhackme-mcp/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

An unofficial [Model Context Protocol](https://modelcontextprotocol.io) server for [TryHackMe](https://tryhackme.com). Search rooms, study tasks with an AI tutor, follow learning paths, check your progress and leaderboard rank, and start or stop lab machines, all from Claude or any MCP client.

```
You:    What should I study next? Start the machine for it.
Claude: → thm_my_next_rooms()
        → thm_start_machine(room_code="furthernmap")
        Next in your Jr Penetration Tester path is "Nmap" (90 min). The machine is
        booting; I'll check its IP in a minute...
```

> **Not affiliated with TryHackMe.** TryHackMe has no official public API. This server uses the same `tryhackme.com/api/v2` endpoints the website calls in your browser. They're undocumented and can change. See [Disclaimer](#disclaimer).

## Documentation

📚 **[Full docs](docs/README.md)**: [Getting started](docs/getting-started.md) · [Authentication](docs/authentication.md) · [Tools reference](docs/tools.md) · [Recipes](docs/recipes.md) · [Troubleshooting](docs/troubleshooting.md) · [FAQ](docs/faq.md)

## Contents

- [Features](#features)
- [Quick start](#quick-start)
- [Authentication](#authentication)
- [Tools](#tools)
- [Prompts](#prompts)
- [Usage examples](#usage-examples)
- [How it works](#how-it-works)
- [Security & privacy](#security--privacy)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Disclaimer](#disclaimer)

## Features

- **34 tools and 3 prompts** covering rooms, tasks, modules, paths, search, leaderboards, profiles, your stats and progress, recommendations, weekly missions, and lab machines.
- **Zero setup for public content.** Add your session cookie for personal data.
- **Safe by default.** The 28 read-only tools carry `readOnlyHint`. The 6 tools that change your account only exist when you set `THM_ALLOW_WRITES=1`, and they're marked so your client asks before running them.
- **Privacy-filtered.** Your email, phone number and tokens are stripped before anything reaches the model.
- **Teaching-first.** It explains room content and gives hints; it never fetches or submits answers.
- **Clean Markdown** with code blocks preserved, so commands copy straight into a terminal.
- stdio, SSE and streamable-HTTP transports.

## Quick start

You need [uv](https://docs.astral.sh/uv/getting-started/installation/) (`brew install uv` on macOS).

### Option 1: Claude Desktop extension (one click)

Download `tryhackme-mcp-vX.Y.Z.mcpb` from the [latest release](https://github.com/realarmaansidhu/tryhackme-mcp/releases/latest) and double-click it. Claude Desktop asks for your (optional) session cookie and stores it in your OS keychain.

### Option 2: Any MCP client (from PyPI)

Add this to your client's MCP config. For Claude Desktop that's `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS or `%APPDATA%\Claude\claude_desktop_config.json` on Windows.

```json
{
  "mcpServers": {
    "tryhackme": {
      "command": "uvx",
      "args": ["tryhackme-mcp"],
      "env": {
        "THM_SESSION": "your_connect_sid_here",
        "THM_ALLOW_WRITES": "0"
      }
    }
  }
}
```

Replace `your_connect_sid_here` with your cookie ([how](#authentication)), or leave it as is for public content only. Quit Claude Desktop fully (Cmd+Q) and reopen it.

<details>
<summary>Claude Code, Cursor, VS Code, Windsurf</summary>

**Claude Code**
```bash
claude mcp add tryhackme -e THM_SESSION=your_connect_sid_here -- uvx tryhackme-mcp
```

**Cursor** (`~/.cursor/mcp.json`), **Windsurf**, **VS Code** (`.vscode/mcp.json`, under `"servers"`): use the same `command`, `args` and `env` as above.
</details>

### Option 3: From source

```bash
git clone https://github.com/realarmaansidhu/tryhackme-mcp.git
cd tryhackme-mcp
uv sync
```

Then point your client at it. See [`examples/claude_desktop_config.local-dev.json`](examples/claude_desktop_config.local-dev.json).

> **Claude Desktop can't find `uv`/`uvx`?** Use the absolute path from `which uvx` (often `/opt/homebrew/bin/uvx`).

## Authentication

Public tools need nothing. For `thm_my_*` tools, premium rooms your subscription covers, and machine control:

1. Log in at [tryhackme.com](https://tryhackme.com).
2. Open DevTools (F12 or Cmd+Opt+I) → **Application** (Chrome, Brave, Edge) or **Storage** (Firefox) → **Cookies** → `https://tryhackme.com`.
3. Copy the value of **`connect.sid`** (it starts with `s%3A`).
4. Paste it as `THM_SESSION` in your config, in place of `your_connect_sid_here`.

Steps for Firefox and Safari, the `THM_COOKIE` fallback, and the `.mcpb` keychain flow are in [docs/authentication.md](docs/authentication.md).

| Variable | Default | Purpose |
|---|---|---|
| `THM_SESSION` | — | Your `connect.sid` cookie |
| `THM_COOKIE` | — | Alternative: the full `Cookie` header, if `connect.sid` alone stops working |
| `THM_ALLOW_WRITES` | `0` | `1` registers the six account-changing tools |

The cookie is a full login. Never commit it or share it. If it leaks, log out of all sessions on TryHackMe. Use `thm_check_auth` to see whether it's still valid.

## Tools

Any `room_code` / `path_code` / `module_code` / `username` argument also accepts a full tryhackme.com URL.

### Public (no login)

| Tool | What it does |
|---|---|
| `thm_search` | Search rooms, paths, modules or networks (`kind`, `difficulty`, `order`, paging) |
| `thm_room_overview` | Room metadata, upvotes and task list |
| `thm_get_task` | One task as Markdown: content, commands, questions, hints |
| `thm_room_full` | The whole room as one Markdown document |
| `thm_room_questions` | Every question and hint in a room, with no answers (for revision) |
| `thm_module` | A module's rooms, in order |
| `thm_path_outline` | A learning path's modules and rooms |
| `thm_leaderboard` | Top 50 monthly or all-time, worldwide or by country |
| `thm_public_profile` | Any user's level, rank, points, streak and path |
| `thm_compare_profiles` | Two users side by side |
| `thm_profile_completed_rooms` | Rooms a user has completed |
| `thm_profile_badges` | Badges with rarity |
| `thm_profile_certificates` | Public certificates |
| `thm_profile_skills` | Top tools and this year's activity |

### Your account (needs `THM_SESSION`)

| Tool | What it does |
|---|---|
| `thm_check_auth` | Is your login valid? (safe fields only) |
| `thm_my_stats` | Level, rank, points (total and this month), rooms, badges, streak, league |
| `thm_my_current_path` | Enrolled path, % done, hours, estimated finish |
| `thm_my_next_rooms` | The next unfinished rooms in your path |
| `thm_my_current_module` | The module you're working through |
| `thm_my_rooms` | Your joined rooms: all, in-progress or completed |
| `thm_my_room_progress` | % complete for up to 50 rooms |
| `thm_my_recommendations` | Rooms TryHackMe recommends for you |
| `thm_my_capability_score` | Capability score components and trends |
| `thm_my_weekly_missions` | Weekly targets vs. your progress |
| `thm_my_notifications` | Notifications (doesn't mark them read) |
| `thm_my_social` | Followers and following |
| `thm_my_running_machines` | Running machines with IP, state, expiry and id |
| `thm_my_streak` | Streak progression |

### Account changes (needs `THM_SESSION` and `THM_ALLOW_WRITES=1`)

| Tool | What it does | |
|---|---|---|
| `thm_start_machine` | Start a room's target machine (first task with a VM, or `task_no`) | |
| `thm_extend_machine` | Add 1 hour to a running machine | |
| `thm_terminate_machine` | Terminate a running machine | destructive |
| `thm_vote_room` | Recommend a room, or withdraw your recommendation | |
| `thm_join_room` | Join a room | experimental |
| `thm_leave_room` | Leave a room | destructive, experimental |

There's deliberately **no answer-submission tool**. Submitting answers should be you, not your AI.

Endpoints behind every tool are documented in [docs/API.md](docs/API.md).

## Prompts

These appear in your client's prompt menu (Claude Desktop: **+** → tryhackme).

| Prompt | What it does |
|---|---|
| `study_room(room_code)` | Tutor mode: explains a room task by task, asks its questions, hints instead of answers |
| `quiz_me(room_code)` | Writes 8 fresh questions to check real understanding |
| `weekly_plan(hours)` | A day-by-day plan from your path, next rooms and weekly missions |

## Usage examples

- "Find free, easy rooms about privilege escalation."
- "Teach me task 4 of `linuxfundamentalspart1`, then quiz me. No answers."
- "What should I do next in my path? Plan my week around 6 hours."
- "Start the machine for `furthernmap` and tell me its IP when it's up."
- "Add an hour to my machine." / "Terminate my machine."
- "Show the Canadian monthly leaderboard. Where do I rank?"
- "Compare my profile with `tryhackme`'s."
- "List the rooms in the `linux-fundamentals` module."

## How it works

```
Claude ──MCP (stdio)──> tryhackme-mcp ──HTTPS + your cookie──> tryhackme.com/api/v2/*
```

- Reads are plain `GET`s to the same JSON endpoints the website uses.
- Module pages have no JSON endpoint, so their room list is read from the schema.org JSON-LD embedded in the page.
- Writes follow the website's own flow: fetch a CSRF token from `/api/v2/auth/csrf`, then `POST` with a `csrf-token` header.
- Rooms have a URL slug and an internal code, which sometimes differ. Machine and vote calls resolve the internal code first.

## Security & privacy

- Your cookie is sent only to `https://tryhackme.com`. Redirects aren't followed.
- `/users/self` contains your email, phone number and Discord token. Only `username`, `isPremium`, `accountType`, `dateSignUp`, `verified`, `roles` and 2FA status get through, and tests enforce that.
- Your own past answers are hidden unless you pass `include_my_answers=true`.
- Account-changing tools don't exist unless `THM_ALLOW_WRITES=1`. When they do, they're annotated non-read-only, and destructive where relevant.
- No telemetry. Nothing is contacted except tryhackme.com.

See [SECURITY.md](SECURITY.md).

## Troubleshooting

| Symptom | Fix |
|---|---|
| Server missing in Claude Desktop | Check `~/Library/Logs/Claude/mcp-server-tryhackme.log`. Usually `uvx` isn't on Claude's PATH, so use the absolute path |
| `401 ... missing or expired` | Copy a fresh `connect.sid` and restart your client |
| `No tasks returned for room` | Premium room without login, or a wrong code. Try `thm_search` |
| `bot protection answered` | TryHackMe challenged the request. Wait and retry, and don't hammer it |
| `Write actions are disabled` | Set `THM_ALLOW_WRITES=1` and restart |
| `endpoint may have changed` | TryHackMe changed its API. [Open an issue](../../issues/new?template=endpoint_changed.md) |

Inspect tools interactively:

```bash
npx @modelcontextprotocol/inspector uvx tryhackme-mcp
```

## Development

```bash
uv sync --extra dev
uv run pytest -q        # fully offline; every HTTP call is mocked
```

```
src/tryhackme_mcp/
  client.py      HTTP client: cookies, CSRF, write gate, error mapping
  formatting.py  JSON/HTML → Markdown, privacy whitelist
  server.py      MCP tools, prompts, CLI
tests/           offline tests (respx)
docs/API.md      endpoint reference
manifest.json    Claude Desktop extension (.mcpb) manifest
server.json      MCP Registry metadata
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for adding tools and cutting releases.

## Disclaimer

This is an independent community project. It is not affiliated with, endorsed by or supported by TryHackMe Ltd. It relies on undocumented endpoints that may change without notice. Use it with your own account, at a human pace, and in line with TryHackMe's Terms of Service. It's for studying and managing your own learning, not for bulk scraping, redistributing premium content, or automating answers.

## License

MIT. See [LICENSE](LICENSE).
