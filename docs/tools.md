# Tools reference

Every tool returns Markdown the assistant can read and quote. Arguments named `room_code`, `path_code`, `module_code` or `username` also accept a full tryhackme.com URL, so pasting a link works.

**Legend:** 🌐 public (no login) · 🔑 needs `THM_SESSION` · ✏️ needs `THM_SESSION` + `THM_ALLOW_WRITES=1`

- [Discovery](#discovery): search, overview, tasks, questions, modules, paths
- [Community](#community): leaderboard, profiles
- [Your account](#your-account)
- [Machines & account changes](#machines--account-changes)
- [Prompts](#prompts)

---

## Discovery

### `thm_search` 🌐
Search rooms, learning paths, modules or networks.

| Arg | Type | Default | Notes |
|---|---|---|---|
| `query` | string | `""` | Keyword; empty lists everything of that kind |
| `kind` | `rooms` \| `paths` \| `modules` \| `networks` \| `all` | `rooms` | |
| `difficulty` | `all` \| `info` \| `easy` \| `medium` \| `hard` \| `insane` | `all` | |
| `order` | `relevance` \| `most-popular` \| `newest` | `relevance` | |
| `page`, `limit` | int | `1`, `12` | `limit` max 50 |

```
**98 results** (page 1 of 25)

- **Nmap** (`furthernmap`, rooms) — easy, walkthrough, free, 50 min
  An in depth look at scanning with Nmap, a powerful network scanning tool.
- **Nmap Basic Port Scans** (`nmap02`, rooms) — easy, walkthrough, free, 2h 0m
  Learn in-depth how nmap TCP connect scan, TCP SYN port scan, and UDP port scan work.
```

### `thm_room_overview` 🌐
A room's metadata (difficulty, type, access, creators, users, upvotes, tags, paths) and task list. With login, it also shows how many questions you've answered per task.

| Arg | Type |
|---|---|
| `room_code` | string |

```
# Linux Fundamentals (Pt1)
- Code: `linuxfundamentalspart1` · https://tryhackme.com/room/linuxfundamentalspart1
- Difficulty: easy · Type: walkthrough
- Access: free
- Joined by: 1,325,225 users
- Upvotes: 898

## Tasks
1. Introduction (1 questions)
2. Talking to Linux (2 questions)
...
```

### `thm_get_task` 🌐
One task as Markdown: the teaching text, command snippets, tables and images, then the questions.

| Arg | Type | Default | Notes |
|---|---|---|---|
| `room_code` | string | | |
| `task_no` | int | | 1-based |
| `include_hints` | bool | `true` | TryHackMe's own hints |
| `include_my_answers` | bool | `false` | 🔑 Shows answers **you** already submitted |

### `thm_room_full` 🌐
The whole room (overview plus every task) as one Markdown document. Good for making study notes. Args: `room_code`, `include_hints`.

### `thm_room_questions` 🌐
Just the questions (and hints) from every task, with no teaching text and no answers. For revision and self-quizzing. Args: `room_code`, `include_hints`.

### `thm_module` 🌐
A module's description and its rooms in order. Find codes with `thm_search(kind="modules")`. Arg: `module_code`.

```
# Linux Fundamentals
...
## Rooms
1. Linux Fundamentals Part 1 (`linuxfundamentalspart1`)
2. Linux Fundamentals Part 2 (`linuxfundamentalspart2`)
3. Linux Fundamentals Part 3 (`linuxfundamentalspart3`)
```

### `thm_path_outline` 🌐
A learning path's modules and rooms in order, with time estimates. With login, rooms show your % progress. Arg: `path_code` (e.g. `jrpenetrationtester`, `presecurity`, `cybersecurity101`).

---

## Community

### `thm_leaderboard` 🌐
Top 50 by points. Banned users are filtered out. With login, it also shows your rank on that board.

| Arg | Type | Default |
|---|---|---|
| `period` | `monthly` \| `alltime` | `monthly` |
| `country` | 2-letter code (`ca`, `us`, `in`…) or empty for worldwide | `""` |
| `limit` | int (≤50) | `25` |

### `thm_public_profile` 🌐
Any user's level, rank, top %, points, rooms, badges, streak, league, capability score and current path. Arg: `username`.

### `thm_compare_profiles` 🌐
Two profiles side by side as a table. Args: `username_a`, `username_b`.

### `thm_profile_completed_rooms` 🌐 · `thm_profile_badges` 🌐
Paginated lists for any user. Args: `username`, `page`, `limit`.

### `thm_profile_certificates` 🌐
A user's public certificates with dates and links. Arg: `username`.

### `thm_profile_skills` 🌐
A user's top tools and this year's activity (active days, events). Arg: `username`.

---

## Your account

All need `THM_SESSION`. None of them change anything.

| Tool | Returns | Args |
|---|---|---|
| `thm_check_auth` | Whether your login works; username, plan, 2FA status | — |
| `thm_my_stats` | Level, rank, top %, points (total + this month), rooms, modules, badges, streak, weekly league | — |
| `thm_my_current_path` | Enrolled path, % done, hours done/total, study plan, estimated finish | — |
| `thm_my_next_rooms` | The next unfinished rooms in your path, in order, with partial progress | `limit` |
| `thm_my_current_module` | The module you're on and its % | — |
| `thm_my_rooms` | Rooms you've joined, with ✅/⏳ | `status` (`all`/`in-progress`/`completed`), `search`, `page`, `limit` |
| `thm_my_room_progress` | % complete for each room you list | `room_codes` (≤50) |
| `thm_my_recommendations` | TryHackMe's personal room recommendations | `limit` |
| `thm_my_capability_score` | Capability score and its components (foundation, activity, specialism, …) with trend arrows | — |
| `thm_my_weekly_missions` | This week's targets (rooms, questions, streak days) vs. your progress | — |
| `thm_my_notifications` | Notifications; reading them does **not** mark them as read | `unread_only`, `limit` |
| `thm_my_social` | Follower/following counts, or either list | `list_type` (`counts`/`followers`/`following`), `page` |
| `thm_my_running_machines` | Running machines: name, room, state, private IP, expiry, id | — |
| `thm_my_streak` | Streak progression (raw) | — |

---

## Machines & account changes

These tools only exist when `THM_ALLOW_WRITES=1`. Clients see them as non-read-only, so they normally ask you first.

| Tool | What it does | Args |
|---|---|---|
| `thm_start_machine` | Starts a room's target machine. It boots in 1–3 minutes; then `thm_my_running_machines` shows the IP | `room_code`, `task_no` (optional: which task's machine) |
| `thm_extend_machine` | +1 hour. TryHackMe may refuse while plenty of time is left | `machine_id` (optional if only one is running) |
| `thm_terminate_machine` ⚠️ | Terminates a machine; anything on it is lost | `machine_id` (optional if only one is running) |
| `thm_vote_room` | Recommend a room (`recommend=true`) or withdraw it (`false`) | `room_code`, `recommend` |
| `thm_join_room` 🧪 | Join a room | `room_code` |
| `thm_leave_room` ⚠️🧪 | Leave a room | `room_code` |

⚠️ destructive · 🧪 experimental (request format inferred, not yet confirmed against the live site)

There's no tool for submitting answers, on purpose. See the [FAQ](faq.md#can-it-answer-questions-for-me).

---

## Prompts

Prompts are ready-made workflows. In Claude Desktop, click **+** → **tryhackme**.

| Prompt | Args | What happens |
|---|---|---|
| `study_room` | `room_code` | The AI tutors you through the room task by task, asks each question, gives hints rather than answers, and waits for you before moving on |
| `quiz_me` | `room_code` | The AI writes 8 new questions (multiple choice, "what does this command do", scenarios) and asks them one at a time |
| `weekly_plan` | `hours` | The AI builds a day-by-day plan from your path, next rooms and weekly missions |
