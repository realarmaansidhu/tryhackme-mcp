# Changelog

## 0.1.0 — unreleased

First release.

- **28 read-only tools:** search, rooms (overview, task, full export, questions), modules, paths,
  leaderboards, public profiles (profile, compare, completed rooms, badges, certificates, skills),
  and account tools (`thm_my_*`: stats, current path, next rooms, current module, my rooms, room
  progress, recommendations, capability score, weekly missions, notifications, social, running
  machines, streak).
- **6 opt-in write tools** (`THM_ALLOW_WRITES=1`): start/extend/terminate machine, vote, join/leave room.
  CSRF handled the way the website does it.
- 3 prompts: `study_room`, `quiz_me`, `weekly_plan`.
- Session auth via `THM_SESSION` or `THM_COOKIE`; placeholder values are ignored.
- Privacy whitelist for `/users/self`; own answers hidden unless requested.
- stdio, SSE and streamable-HTTP transports.
- Claude Desktop extension manifest (`.mcpb`) and MCP Registry metadata (`server.json`).
- Endpoints mapped from the live site on 2026-11-22.
