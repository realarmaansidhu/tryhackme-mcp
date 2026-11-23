# Authentication

Public tools (search, rooms, tasks, paths, modules, leaderboards, public profiles) need **no login**. You only need this page for:

- `thm_my_*` tools: your stats, path progress, recommendations, missions, machines
- premium rooms your subscription covers
- account changes: starting machines, voting, joining rooms

## Why a cookie and not an API key?

TryHackMe has no personal API keys or "Sign in with TryHackMe" (OAuth) for individual users. Its only official API is an Enterprise product for companies. So this server does what your browser does: it sends your **session cookie** (`connect.sid`) with each request.

That cookie is a full login to your account. Treat it like a password.

## Get your cookie

### Chrome, Brave, Edge, Arc, Opera

1. Log in at [tryhackme.com](https://tryhackme.com).
2. Open DevTools: **Cmd+Option+I** (macOS) or **F12** / **Ctrl+Shift+I** (Windows/Linux).
3. Go to the **Application** tab (click `»` if it's hidden).
4. In the left sidebar: **Storage → Cookies → `https://tryhackme.com`**.
5. Click the **`connect.sid`** row and copy the **Cookie Value** shown at the bottom. It starts with `s%3A`.

### Firefox

1. Log in at tryhackme.com.
2. **Cmd+Option+I** / **F12** → **Storage** tab → **Cookies** → `https://tryhackme.com`.
3. Double-click the value of **`connect.sid`** and copy it.

### Safari

1. Enable the Develop menu: **Safari → Settings → Advanced → Show features for web developers**.
2. Log in at tryhackme.com, then **Develop → Show Web Inspector** → **Storage** tab → **Cookies**.
3. Copy the value of **`connect.sid`**.

### No `connect.sid`? Use the whole cookie header

If TryHackMe renames its session cookie, or `connect.sid` alone gives `401` errors:

1. DevTools → **Network** tab → reload the page.
2. Click any request whose URL contains `api/v2`.
3. Under **Request Headers**, copy the entire value of **`cookie`**.
4. Put it in `THM_COOKIE` instead of `THM_SESSION`. `THM_COOKIE` wins if both are set.

## Put it in your config

**Claude Desktop extension (.mcpb):** paste it into the "TryHackMe session cookie" field during install, or later under **Settings → Extensions → TryHackMe**. It's stored in your OS keychain.

**Config file** (Claude Desktop, Cursor, …): replace the placeholder:

```json
"env": {
  "THM_SESSION": "s%3AaBcD...the rest of your value...",
  "THM_ALLOW_WRITES": "0"
}
```

**Claude Code:**

```bash
claude mcp remove tryhackme -s user
claude mcp add tryhackme -s user -e THM_SESSION='s%3AaBcD...' -- uvx tryhackme-mcp
```

**From source / `.env`:** copy `.env.example` to `.env` and fill it in. `.env` is gitignored.

Restart your client, then ask: *"Check my TryHackMe auth."* You should see your username, plan and 2FA status. Your email and other personal fields are never shown.

## Enable account changes (optional)

```json
"THM_ALLOW_WRITES": "1"
```

This registers six more tools: `thm_start_machine`, `thm_extend_machine`, `thm_terminate_machine`, `thm_vote_room`, `thm_join_room`, `thm_leave_room`. They're marked as non-read-only (terminate and leave as destructive), so well-behaved clients ask before running them. Leave it at `0` if you only want to read.

## Environment variables

| Variable | Default | Meaning |
|---|---|---|
| `THM_SESSION` | — | Value of your `connect.sid` cookie |
| `THM_COOKIE` | — | Full `Cookie` header; overrides `THM_SESSION` |
| `THM_ALLOW_WRITES` | `0` | `1` / `true` / `yes` / `on` enables account-changing tools |

The placeholder `your_connect_sid_here` is treated as "not set".

## Keeping your cookie safe

- **Never** commit it, paste it in an issue, or show it in a screenshot or screen share.
- It expires when you log out of TryHackMe, or after a while. If tools start saying `401`, copy a fresh one.
- **Leaked it?** Log out of TryHackMe (or log out of all sessions in account settings). That invalidates it immediately.
- **Turn on 2FA** for your TryHackMe account. A session cookie bypasses 2FA once issued, but 2FA stops someone using a leaked password to mint new ones.
- Be careful with browser extensions while copying it. Anything with "read all site data" permission can see it too.

## What the server does with it

- Sends it only to `https://tryhackme.com`. HTTP redirects aren't followed, so it can't be forwarded elsewhere.
- Doesn't log it, and has no telemetry.
- Strips personal fields (email, phone, Discord token, demographics, subscription IDs) from account responses before the AI sees them.

See [SECURITY.md](../SECURITY.md) for more.
