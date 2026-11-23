# Getting started

This gets the TryHackMe MCP server running in about 5 minutes. You'll start with public content (no login), then optionally add your account.

## 1. Install uv

The server runs on Python, managed by [uv](https://docs.astral.sh/uv/). uv downloads the right Python and dependencies for you, so you don't need to install Python yourself.

| OS | Command |
|---|---|
| macOS | `brew install uv` or `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Linux | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Windows | `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 \| iex"` |

Check it worked, and note the path:

```bash
uvx --version
which uvx        # macOS/Linux, e.g. /opt/homebrew/bin/uvx
where uvx        # Windows
```

## 2. Add the server to your client

Pick your client.

### Claude Desktop: one-click extension (easiest)

1. Download `tryhackme-mcp-vX.Y.Z.mcpb` from the [latest release](https://github.com/realarmaansidhu/tryhackme-mcp/releases/latest).
2. Double-click it. Claude Desktop opens an install dialog.
3. Claude asks for an optional session cookie and whether to allow account changes. You can leave both empty for now.

### Claude Desktop: config file

1. Open the config file:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - Or in Claude Desktop: **Settings → Developer → Edit Config**
2. Add `tryhackme` inside `mcpServers`, next to any servers you already have:

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

   You can leave `your_connect_sid_here` as is. It's a placeholder the server ignores, so you'll get public mode.
3. Quit Claude Desktop completely (**Cmd+Q** on macOS, or right-click the tray icon → Quit on Windows) and reopen it.
4. Click the tools icon in the chat box. You should see **tryhackme** with its tools.

> If the server doesn't appear, Claude Desktop probably can't find `uvx`. Replace `"uvx"` with the full path from step 1, e.g. `"/opt/homebrew/bin/uvx"`.

### Claude Code

```bash
claude mcp add tryhackme -s user -- uvx tryhackme-mcp
claude mcp list          # should show: tryhackme ✓ connected
```

With your cookie:

```bash
claude mcp add tryhackme -s user \
  -e THM_SESSION='your_connect_sid_here' \
  -- uvx tryhackme-mcp
```

Use single quotes. Cookies contain `%` and other characters your shell might interpret.

### Cursor

Create or edit `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (per project):

```json
{
  "mcpServers": {
    "tryhackme": {
      "command": "uvx",
      "args": ["tryhackme-mcp"],
      "env": { "THM_SESSION": "your_connect_sid_here" }
    }
  }
}
```

### VS Code (GitHub Copilot agent mode)

`.vscode/mcp.json`:

```json
{
  "servers": {
    "tryhackme": {
      "type": "stdio",
      "command": "uvx",
      "args": ["tryhackme-mcp"],
      "env": { "THM_SESSION": "your_connect_sid_here" }
    }
  }
}
```

### Windsurf, Zed, LM Studio, others

Any client that supports stdio MCP servers works: command `uvx`, args `["tryhackme-mcp"]`, plus the optional env vars.

### Remote / HTTP clients

```bash
uvx tryhackme-mcp --transport streamable-http --port 8000   # → http://127.0.0.1:8000/mcp
uvx tryhackme-mcp --transport sse --port 8000               # → http://127.0.0.1:8000/sse
```

It binds to localhost only. Don't expose it to the internet with a cookie set: anyone who reaches it can use your account.

## 3. Try it

Ask your assistant:

- *"Search TryHackMe for free beginner rooms about networking."*
- *"Give me an overview of the `furthernmap` room."*
- *"Teach me task 2 of `linuxfundamentalspart1`."*
- *"Show me the Jr Penetration Tester learning path."*

## 4. Add your account (optional)

To get your stats, path progress, recommendations, and machine control, follow [Authentication](authentication.md). It takes about 2 minutes.

## Updating

`uvx` caches the package. To get the newest release:

```bash
uvx --refresh tryhackme-mcp --help
```

Then restart your client. The `.mcpb` extension updates when you install a newer `.mcpb`.

## Uninstalling

Remove the `tryhackme` block from your client config (or the extension in Claude Desktop → Settings → Extensions), then run `uv cache clean tryhackme-mcp`.
