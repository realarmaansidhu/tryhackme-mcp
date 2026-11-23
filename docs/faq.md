# FAQ

### Is this official?
No. It's an independent community project, not affiliated with or endorsed by TryHackMe. TryHackMe doesn't currently offer a public API or an MCP server for individual users.

### How does it work without an API?
It calls the same `tryhackme.com/api/v2` endpoints the TryHackMe website calls in your browser, sending your session cookie like your browser does. See [How it works](../README.md#how-it-works) and the [API reference](API.md).

### Will it break?
Possibly. The endpoints are undocumented and can change whenever TryHackMe updates its site. Errors say clearly when an endpoint looks like it moved; please [report it](https://github.com/realarmaansidhu/tryhackme-mcp/issues/new?template=endpoint_changed.md).

### Is it allowed?
It does what you can already do in your browser, on your own account, at a human pace. Read TryHackMe's Terms of Service yourself. The project draws its own lines: no bot-protection bypass, no bulk scraping, no redistributing premium content, no automated answers. Use it to learn, not to farm points.

### Can it answer questions for me?
No, by design.
- TryHackMe's room API doesn't return answers, and the server doesn't look for them anywhere else.
- There's no answer-submission tool.
- The built-in prompts tell the AI to give hints, not answers.

The AI may still know an answer from its general training. If you want to actually learn, ask for hints.

### Does it see my password, email or payment details?
- **Password:** never. It only uses the session cookie you give it.
- **Email, phone, Discord token, demographics:** TryHackMe returns these on one endpoint. The server strips them before the AI sees anything, and tests enforce this.
- **Payment details:** no endpoint the server uses returns them.

### Where is my cookie stored?
Wherever you put it: your client's config file, a local `.env`, or (with the `.mcpb` extension) your OS keychain. The server only sends it to tryhackme.com.

### Can it hack things for me?
No. It manages your TryHackMe *learning*: content, progress, and starting or stopping your lab machines. It doesn't run tools against targets. You do the hacking, in the lab, where it's legal.

### Do I need a premium subscription?
No. Free rooms, paths, profiles and leaderboards all work. Premium rooms work if your account has access.

### Which AI clients does it work with?
Any MCP client: Claude Desktop, Claude Code, Cursor, VS Code (Copilot), Windsurf, Zed and more. See [Getting started](getting-started.md).

### Can I use it with a team or class?
Each person needs their own cookie; never share one account. For organisations, TryHackMe's official Enterprise API may be a better fit.

### How do I contribute?
See [CONTRIBUTING.md](../CONTRIBUTING.md). New tools are usually under 30 lines plus a test.
