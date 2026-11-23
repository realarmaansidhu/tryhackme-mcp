# TryHackMe MCP: documentation

Welcome! Read the guides in order if you're new, or jump to what you need.

| Guide | Read it when… |
|---|---|
| [Getting started](getting-started.md) | You want it running in Claude (or another client) in 5 minutes |
| [Authentication](authentication.md) | You want your own stats, progress and machines, so you need your session cookie |
| [Tools reference](tools.md) | You want to know every tool, its arguments and what it returns |
| [Recipes](recipes.md) | You want ideas: study a room, plan a week, run a lab, revise for a cert |
| [Troubleshooting](troubleshooting.md) | Something doesn't work |
| [FAQ](faq.md) | Is this official? Is it allowed? Does it do my rooms for me? |
| [API reference](API.md) | You're contributing, or TryHackMe changed something |

## 30-second version

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/).
2. Add this to your MCP client config:
   ```json
   "tryhackme": { "command": "uvx", "args": ["tryhackme-mcp"] }
   ```
3. Restart the client and ask: *"Find beginner TryHackMe rooms about Linux."*

For your own stats and lab machines, add your cookie ([how](authentication.md)).
