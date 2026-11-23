# Troubleshooting

Start here: ask your assistant *"Check my TryHackMe auth"*. If the tool runs at all, the server is installed correctly and the problem is elsewhere.

## The server doesn't show up

| Check | How |
|---|---|
| Client fully restarted? | Claude Desktop must be **quit** (Cmd+Q), not just have its window closed |
| Can the client find `uvx`? | GUI apps often don't see your shell's PATH. Use the full path from `which uvx`, e.g. `/opt/homebrew/bin/uvx` |
| Is the JSON valid? | A missing comma breaks every server in the file. Paste it into a JSON validator |
| What does the log say? | **macOS:** `~/Library/Logs/Claude/mcp-server-tryhackme.log` · **Windows:** `%APPDATA%\Claude\logs\mcp-server-tryhackme.log` |
| Does it run by hand? | `uvx tryhackme-mcp --help` should print usage |

**First launch timed out?** The first run downloads Python and dependencies. Restart the client once and it'll start quickly after that.

## Error messages

| Message | Meaning | Fix |
|---|---|---|
| `This tool needs your TryHackMe login` | No cookie configured (or still the placeholder) | [Add your cookie](authentication.md) |
| `TryHackMe says you're not logged in (401)` | Cookie expired, or you logged out | Copy a fresh `connect.sid` and restart the client |
| `Write actions are disabled` | `THM_ALLOW_WRITES` isn't on | Set it to `1` and restart, if you want write tools |
| `No tasks returned for room` | Premium room without access, or a wrong code | Check with `thm_search`; premium rooms need a subscription |
| `Not found on TryHackMe` | Wrong room/path/module code | Copy the code from the URL, or paste the whole URL |
| `TryHackMe's bot protection answered` | TryHackMe challenged the request (too many too fast, or a flagged network) | Wait a few minutes. The server deliberately doesn't bypass this |
| `TryHackMe refused to extend this machine` | Extensions are usually only allowed near expiry | Try again when ~15 minutes are left |
| `You have several machines running` | Ambiguous machine command | Run `thm_my_running_machines` and pass the `id` |
| `non-JSON` / `endpoint may have changed` / `redirected` | TryHackMe changed its site | [Open an issue](https://github.com/realarmaansidhu/tryhackme-mcp/issues/new?template=endpoint_changed.md) |
| `Couldn't get a CSRF token` | Session expired mid-way | Refresh your cookie |

## Write tools don't appear

They're only registered when `THM_ALLOW_WRITES` is `1`/`true`/`yes`/`on` **at server start**. Change it, then restart the client.

## The AI gives answers to room questions

The server never fetches answers: TryHackMe's room API doesn't return them, and `include_my_answers` only shows answers *you* previously submitted. If the AI "knows" an answer, that's its general knowledge. Tell it "hints only", or use the `study_room` prompt, which asks for that explicitly.

## Debug with the MCP Inspector

```bash
npx @modelcontextprotocol/inspector uvx tryhackme-mcp
```

It opens a web UI where you can call each tool directly and see the raw output. With a cookie:

```bash
THM_SESSION='s%3A...' npx @modelcontextprotocol/inspector uvx tryhackme-mcp
```

## Still stuck?

[Open an issue](https://github.com/realarmaansidhu/tryhackme-mcp/issues/new?template=bug_report.md) with the tool name, the arguments and the error. **Remove your cookie first.**
