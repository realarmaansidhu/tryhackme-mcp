# Security

## Your session cookie

`THM_SESSION` is a full login to your TryHackMe account. Treat it like a password:

- Keep it in your MCP client config or a local `.env` (gitignored), never in code, issues or screenshots.
- If it leaks, log out of all sessions in TryHackMe's account settings; that invalidates it.
- Don't run the HTTP transports on a public interface while a cookie is set.

## What the server does with it

- Sends it only to `https://tryhackme.com`. Redirects are not followed.
- Strips personal fields (email, phone, Discord token, demographics, subscription ids) from
  `/users/self` before anything reaches the model.
- Can't change your account unless you set `THM_ALLOW_WRITES=1`. Write tools are marked
  non-read-only (and destructive where relevant) so MCP clients ask before running them.

## Reporting a vulnerability

Please open a private security advisory on GitHub (Security → Report a vulnerability) rather
than a public issue.

Vulnerabilities in TryHackMe itself are out of scope here; report those to TryHackMe directly.
