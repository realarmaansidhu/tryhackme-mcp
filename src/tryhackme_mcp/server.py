"""TryHackMe MCP server.

Read-only tools over the tryhackme.com web API. Public tools work without login;
tools named thm_my_* need the THM_SESSION env var (your connect.sid cookie).
"""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import date
from typing import Literal

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

from . import __version__

from . import formatting as fmt
from .client import THMClient, THMError, is_authenticated, writes_enabled

mcp = MCPServer(
    "tryhackme",
    version=__version__,
    instructions=(
        "Tools for TryHackMe (tryhackme.com), a cybersecurity learning platform. "
        "Rooms are identified by a room code (the part after /room/ in a URL, e.g. "
        "'linuxfundamentalspart1'); paths by a path code (e.g. 'jrpenetrationtester'). "
        "Use thm_search to find codes. Room content is study material: explain and "
        "teach from it, and do not volunteer answers to room questions unless asked. "
        "thm_my_* tools need the user's login and fail with a clear message without it."
    ),
)

# Every tool is read-only: nothing here changes your TryHackMe account.
READ_ONLY = ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True)


# Write tools change your account. They're only registered when THM_ALLOW_WRITES is on,
# and carry readOnlyHint=False so clients ask before running them.
WRITE = ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True)
DESTRUCTIVE = ToolAnnotations(read_only_hint=False, destructive_hint=True, idempotent_hint=False, open_world_hint=True)


def tool():
    return mcp.tool(annotations=READ_ONLY)


def write_tool(destructive: bool = False):
    def deco(fn):
        if writes_enabled():
            return mcp.tool(annotations=DESTRUCTIVE if destructive else WRITE)(fn)
        return fn
    return deco


_client: THMClient | None = None


def client() -> THMClient:
    global _client
    if _client is None:
        _client = THMClient()
    return _client


def set_client(c: THMClient | None) -> None:
    """Swap the HTTP client (used by tests)."""
    global _client
    _client = c


async def _safe(coro) -> str:
    try:
        return await coro
    except THMError as e:
        return f"Error: {e}"


def _code(s: str) -> str:
    """Accept a room/path code or a full TryHackMe URL."""
    s = (s or "").strip().rstrip("/")
    for marker in ("/room/", "/path/outline/", "/path/", "/p/", "/module/"):
        if marker in s:
            s = s.split(marker, 1)[1]
    return s.split("?")[0].split("/")[0]


# ---------------------------------------------------------------- public: discovery

Kind = Literal["rooms", "paths", "modules", "networks", "all"]
Difficulty = Literal["all", "info", "easy", "medium", "hard", "insane"]


@tool()
async def thm_search(
    query: str = "",
    kind: Kind = "rooms",
    difficulty: Difficulty = "all",
    order: Literal["relevance", "most-popular", "newest"] = "relevance",
    page: int = 1,
    limit: int = 12,
) -> str:
    """Search TryHackMe rooms, learning paths, modules or networks by keyword.

    Returns titles, codes, difficulty, free/premium and estimated time. Use the
    returned code with thm_room_overview / thm_path_outline.
    """
    async def run():
        data = await client().get(
            "/api/v2/hacktivities/extended-search",
            {
                "kind": kind,
                "difficulty": difficulty,
                "order": order,
                "roomType": "all",
                "userProgress": "all",
                "searchText": query,
                "page": max(1, page),
                "limit": max(1, min(limit, 50)),
            },
        )
        return fmt.search_results(data or {}, kind)
    return await _safe(run())


@tool()
async def thm_room_overview(room_code: str) -> str:
    """Get a room's metadata (difficulty, type, creators, tags, paths) and its task list.

    room_code: e.g. 'linuxfundamentalspart1' or a full tryhackme.com/room/... URL.
    """
    code = _code(room_code)

    async def run():
        details, tasks = await asyncio.gather(
            client().get("/api/v2/rooms/details", {"roomCode": code}),
            client().get("/api/v2/rooms/tasks", {"roomCode": code}),
            return_exceptions=True,
        )
        if isinstance(details, Exception):
            raise details
        d = dict(details or {})
        # Votes are keyed by the room's internal code, which can differ from the URL slug.
        try:
            votes = await client().get("/api/v2/rooms/votes", {"roomCode": d.get("code") or code})
            if isinstance(votes, dict) and votes.get("votes") is not None:
                d["_votes"] = votes["votes"]
        except Exception:  # votes are optional decoration
            pass
        return fmt.room_overview(d, tasks if isinstance(tasks, list) else None, slug=code)
    return await _safe(run())


async def _tasks(code: str) -> list[dict]:
    tasks = await client().get("/api/v2/rooms/tasks", {"roomCode": code})
    if not isinstance(tasks, list) or not tasks:
        raise THMError(
            f"No tasks returned for room '{code}'. It may be premium (log in with THM_SESSION) "
            "or the code may be wrong; try thm_search."
        )
    return sorted(tasks, key=lambda t: t.get("taskNo", 0))


@tool()
async def thm_get_task(
    room_code: str,
    task_no: int,
    include_hints: bool = True,
    include_my_answers: bool = False,
) -> str:
    """Get one task of a room as Markdown: the teaching content, commands, and questions.

    include_hints: show the hints TryHackMe attaches to questions.
    include_my_answers: show answers YOU already submitted (needs login). Off by default.
    """
    code = _code(room_code)

    async def run():
        tasks = await _tasks(code)
        for t in tasks:
            if t.get("taskNo") == task_no:
                return fmt.task_md(t, include_hints=include_hints, include_my_answers=include_my_answers)
        nums = ", ".join(str(t.get("taskNo")) for t in tasks)
        raise THMError(f"Room '{code}' has no task {task_no}. Tasks: {nums}")
    return await _safe(run())


@tool()
async def thm_room_full(room_code: str, include_hints: bool = True) -> str:
    """Export a whole room (overview + every task + questions) as one Markdown document."""
    code = _code(room_code)

    async def run():
        details = await client().get("/api/v2/rooms/details", {"roomCode": code})
        tasks = await _tasks(code)
        parts = [fmt.room_overview(details or {}, None, slug=code)]
        parts += [fmt.task_md(t, include_hints=include_hints) for t in tasks]
        return "\n\n---\n\n".join(parts)
    return await _safe(run())


@tool()
async def thm_path_outline(path_code: str) -> str:
    """Get a learning path's modules and rooms in order, with time estimates.

    With login, rooms show your progress percentage.
    path_code: e.g. 'jrpenetrationtester', 'beginner', 'presecurity', or a path URL.
    """
    code = _code(path_code)

    async def run():
        data = await client().get("/api/v2/paths/outline", {"pathCode": code})
        return fmt.path_outline(data or {})
    return await _safe(run())


# ---------------------------------------------------------------- public: profiles

@tool()
async def thm_public_profile(username: str) -> str:
    """Get any user's public TryHackMe profile: level, rank, points, rooms, badges, streak, path."""
    u = _code(username)

    async def run():
        return fmt.public_profile(await client().get("/api/v2/public-profile", {"username": u}) or {})
    return await _safe(run())


@tool()
async def thm_profile_completed_rooms(username: str, page: int = 1, limit: int = 25) -> str:
    """List the rooms a user has completed (public profile data)."""
    u = _code(username)

    async def run():
        data = await client().get(
            "/api/v2/public-profile/completed-rooms",
            {"username": u, "page": max(1, page), "limit": max(1, min(limit, 100))},
        )
        return fmt.paged_list(
            data or {},
            lambda r: f"- {r.get('title')} (`{r.get('code')}`, {r.get('difficulty')}, {r.get('type')})",
        )
    return await _safe(run())


@tool()
async def thm_profile_badges(username: str, page: int = 1, limit: int = 25) -> str:
    """List a user's earned badges with rarity."""
    u = _code(username)

    async def run():
        data = await client().get(
            "/api/v2/public-profile/badges",
            {"username": u, "page": max(1, page), "limit": max(1, min(limit, 100))},
        )
        return fmt.paged_list(
            data or {},
            lambda b: f"- **{b.get('title') or b.get('name')}** — {b.get('description', '').strip()}"
            + (f" ({b.get('rarityTier')}, {b.get('rarityPercent')}% of users)" if b.get("rarityTier") else ""),
        )
    return await _safe(run())


@tool()
async def thm_profile_certificates(username: str) -> str:
    """List a user's public TryHackMe certificates (path completions, SAL1, etc.)."""
    u = _code(username)

    async def run():
        data = await client().get(
            "/api/v2/certificates/public-list",
            {"username": u, "page": 1, "limit": 50, "sort": "newest"},
        )
        return fmt.paged_list(
            data or {},
            lambda c: f"- {c.get('name')} — {str(c.get('achieved', ''))[:10]}"
            + (f" · {c['url']}" if c.get("url") else ""),
        )
    return await _safe(run())


@tool()
async def thm_profile_skills(username: str) -> str:
    """Show a user's top tools and yearly activity summary."""
    u = _code(username)

    async def run():
        tools, year = await asyncio.gather(
            client().get("/api/v2/public-profile/top-tools", {"username": u}),
            client().get(
                "/api/v2/public-profile/yearly-activity", {"username": u, "year": date.today().year}
            ),
            return_exceptions=True,
        )
        out = [f"# {u}: skills & activity"]
        if isinstance(tools, dict) and tools.get("tools"):
            out.append("\n## Top tools")
            out += [f"- {t.get('label')} ({t.get('categoryLabel')})" for t in tools["tools"]]
        if isinstance(year, dict) and year.get("yearlyActivity") is not None:
            days = [d for d in year["yearlyActivity"] if d.get("count")]
            out.append(
                f"\n## {date.today().year} activity\n- Total events: {year.get('totalCount', 0)}"
                f"\n- Active days: {len(days)}"
            )
        if len(out) == 1:
            raise THMError(f"No skills data for '{u}' (profile may be private).")
        return "\n".join(out)
    return await _safe(run())


# ---------------------------------------------------------------- authenticated

@tool()
async def thm_check_auth() -> str:
    """Check whether a TryHackMe login is configured and still valid."""
    if not is_authenticated():
        return (
            "Not logged in. Public tools work; thm_my_* tools need THM_SESSION "
            "(your connect.sid cookie). See README > Authentication."
        )

    async def run():
        data = await client().get("/api/v2/users/self", auth=True)
        user = (data or {}).get("user") or {}
        return "Logged in.\n" + json.dumps(fmt.safe_self(user), indent=2)
    return await _safe(run())


@tool()
async def thm_my_stats() -> str:
    """Your own stats: level, rank, points (total + this month), rooms, modules, badges, streak, league."""
    async def run():
        stats, points, league = await asyncio.gather(
            client().get("/api/v2/users/statistics", auth=True),
            client().get("/api/v2/users/points", auth=True),
            client().get("/api/v2/weekly-leagues/statistics", {"minimal": "true"}, auth=True),
            return_exceptions=True,
        )
        if isinstance(stats, Exception):
            raise stats
        s = stats or {}
        out = [
            "# Your TryHackMe stats",
            f"- Level: {s.get('level')}",
            f"- Rank: {s.get('rank')} (top {s.get('topPercentage')}%)",
            f"- Points: {s.get('totalPoints')}",
            f"- Rooms completed: {s.get('completedRoomsNumber')}",
            f"- Modules completed: {s.get('completedModulesNumber')}",
            f"- Badges: {s.get('badgesNumber')}",
            f"- Streak: {s.get('streak')} days",
        ]
        if isinstance(points, dict):
            out.append(f"- Points this month: {points.get('monthlyPoints')}")
        if isinstance(league, dict):
            out.append(
                f"- Weekly league: tier {league.get('tier')}, position {league.get('position')}, "
                f"ends {str(league.get('endDate', ''))[:10]}"
            )
        return "\n".join(out)
    return await _safe(run())


@tool()
async def thm_my_current_path() -> str:
    """Your enrolled learning path, completion %, hours done and estimated finish date."""
    async def run():
        cur, prog = await asyncio.gather(
            client().get("/api/v2/paths/current", auth=True),
            client().get("/api/v2/path/progress", auth=True),
            return_exceptions=True,
        )
        if isinstance(cur, Exception):
            raise cur
        p = (cur or {}).get("path") or {}
        if not p:
            return "You're not enrolled in a learning path."
        out = [
            f"# {p.get('title')} (`{p.get('code')}`)",
            f"- Progress: {(cur or {}).get('progress')}%",
            f"- Difficulty: {p.get('difficulty')}",
        ]
        if isinstance(prog, dict):
            out += [
                f"- Hours: {prog.get('completedHours')} of {prog.get('totalPathHours')}",
                f"- Study plan: {prog.get('hoursPerWeek')} h/week, est. finish "
                f"{str(prog.get('estimatedCompletionDate', ''))[:10]}",
            ]
        out.append(f"\nUse thm_path_outline('{p.get('code')}') for the full module list.")
        return "\n".join(out)
    return await _safe(run())


@tool()
async def thm_my_room_progress(room_codes: list[str]) -> str:
    """Your completion % for one or more rooms (max 50)."""
    codes = [_code(c) for c in room_codes][:50]

    async def run():
        if not codes:
            raise THMError("Give at least one room code.")
        data = await client().get(
            "/api/v2/hacktivities/search-progress", {"roomCodes": ",".join(codes)}, auth=True
        )
        rows = {r.get("roomCode"): r.get("progressPercentage", 0) for r in (data or {}).get("roomProgress") or []}
        return "\n".join(f"- `{c}`: {rows.get(c, 0)}%" for c in codes)
    return await _safe(run())


@tool()
async def thm_my_running_machines() -> str:
    """List your currently running TryHackMe machines (VMs): id, room, state, private IP, expiry."""
    async def run():
        vms = await client().get("/api/v2/vms/running", auth=True)
        if not vms:
            return "No machines running."
        return "\n".join(fmt.machine(v) for v in vms)
    return await _safe(run())


@tool()
async def thm_my_streak() -> str:
    """Your streak and weekly mission progression."""
    async def run():
        data = await client().get("/api/v2/users/missions/streak-progression", auth=True)
        return "```json\n" + json.dumps(data, indent=2)[:4000] + "\n```"
    return await _safe(run())


# ---------------------------------------------------------------- more public tools

@tool()
async def thm_module(module_code: str) -> str:
    """Get a module (a themed group of rooms, e.g. 'linux-fundamentals') and its rooms in order.

    module_code: e.g. 'linux-fundamentals' or a tryhackme.com/module/... URL.
    Find codes with thm_search(kind='modules').
    """
    code = _code(module_code)

    async def run():
        html = await client().get_html(f"/module/{code}")
        mod = fmt.module_from_html(html, code)
        if not mod:
            raise THMError(f"Couldn't read module '{code}'. Check the code with thm_search(kind='modules').")
        return fmt.module_md(mod)
    return await _safe(run())


@tool()
async def thm_room_questions(room_code: str, include_hints: bool = True) -> str:
    """Only the questions (and hints) of every task in a room, for revision or quizzing.

    No teaching content and no answers. Pair with thm_get_task to study a task first.
    """
    code = _code(room_code)

    async def run():
        tasks = await _tasks(code)
        out = [f"# Questions: `{code}`"]
        for t in tasks:
            qs = t.get("questions") or []
            if not qs:
                continue
            out.append(f"\n## Task {t.get('taskNo')}: {t.get('title', '')}")
            for q in qs:
                p = q.get("progress") or {}
                if p.get("noAnswer"):
                    continue
                done = " ✅" if p.get("correct") else ""
                out.append(f"{q.get('questionNo')}. {fmt.html_to_md(q.get('question'))}{done}")
                if include_hints and q.get("hint"):
                    out.append(f"   - Hint: {q['hint'].strip()}")
        return "\n".join(out) if len(out) > 1 else f"Room `{code}` has no questions that need answers."
    return await _safe(run())


@tool()
async def thm_leaderboard(
    period: Literal["monthly", "alltime"] = "monthly",
    country: str = "",
    limit: int = 25,
) -> str:
    """TryHackMe's points leaderboard (top 50), worldwide or for one country.

    country: two-letter code, e.g. 'ca', 'us', 'in'. Empty = worldwide.
    With login, also shows your own rank on that board.
    """
    async def run():
        data = await client().get(
            "/api/v2/leaderboards/general", {"period": period, "country": country.lower().strip()}
        )
        return fmt.leaderboard(data or {}, period, country, max(1, min(limit, 50)))
    return await _safe(run())


@tool()
async def thm_compare_profiles(username_a: str, username_b: str) -> str:
    """Compare two users' public profiles side by side (level, rank, points, rooms, badges, streak)."""
    a, b = _code(username_a), _code(username_b)

    async def run():
        pa, pb = await asyncio.gather(
            client().get("/api/v2/public-profile", {"username": a}),
            client().get("/api/v2/public-profile", {"username": b}),
        )
        return fmt.compare(pa or {}, pb or {})
    return await _safe(run())


# ---------------------------------------------------------------- more authenticated tools

async def _my_id() -> str:
    data = await client().get("/api/v2/users/self", auth=True)
    uid = ((data or {}).get("user") or {}).get("_id")
    if not uid:
        raise THMError("Couldn't read your user id from TryHackMe.")
    return uid


@tool()
async def thm_my_next_rooms(limit: int = 5) -> str:
    """What to study next: the first unfinished rooms in your enrolled learning path, in order."""
    async def run():
        cur = await client().get("/api/v2/paths/current", auth=True)
        p = (cur or {}).get("path") or {}
        if not p.get("code"):
            return "You're not enrolled in a learning path. Browse with thm_search(kind='paths')."
        outline = await client().get("/api/v2/paths/outline", {"pathCode": p["code"]}, auth=True)
        todo = []
        for m in (outline or {}).get("modules") or []:
            for r in m.get("rooms") or []:
                if (r.get("progressPercentage") or 0) < 100:
                    todo.append((m.get("title"), r))
        if not todo:
            return f"You've finished every room in {p.get('title')}. 🎉"
        out = [f"# Next up in {p.get('title')} ({(cur or {}).get('progress')}% done)"]
        for mod, r in todo[: max(1, min(limit, 20))]:
            pct = r.get("progressPercentage") or 0
            out.append(
                f"- **{r.get('title')}** (`{r.get('code')}`) · module: {mod} · "
                f"{fmt.minutes(r.get('timeToComplete'))}" + (f" · {pct}% started" if pct else "")
            )
        return "\n".join(out)
    return await _safe(run())


@tool()
async def thm_my_current_module() -> str:
    """The module you're currently working through, with your progress."""
    async def run():
        mods = await client().get("/api/v2/paths/current-module", auth=True)
        if not mods:
            return "No current module."
        return "\n".join(
            f"- **{m.get('title')}** (`{m.get('code')}`, {m.get('type')}) — {m.get('progress')}% done"
            for m in mods
        )
    return await _safe(run())


@tool()
async def thm_my_recommendations(limit: int = 8) -> str:
    """Rooms TryHackMe recommends for you, with difficulty and time."""
    async def run():
        data = await client().get(
            "/api/v2/recommendations",
            {"contentType": "room", "contentSubType": "challenge", "recMethod": "embedding",
             "surface": "challenge-page-v2"},
            auth=True,
        )
        recs = sorted((data or {}).get("recommendations") or [], key=lambda r: r.get("order", 0))
        codes = [r["value"] for r in recs if r.get("value") and not r.get("is_dismissed")]
        codes = codes[: max(1, min(limit, 10))]
        if not codes:
            return "No recommendations right now."
        details = await asyncio.gather(
            *(client().get(f"/api/v2/recommendations/details/{c}", auth=True) for c in codes),
            return_exceptions=True,
        )
        out = ["# Recommended for you"]
        for c, d in zip(codes, details):
            if isinstance(d, dict):
                out.append(f"- **{d.get('title', c)}** (`{c}`) — {d.get('difficulty', '?')}, "
                           f"{fmt.minutes(d.get('timeToComplete'))}. {(d.get('description') or '').strip()}")
            else:
                out.append(f"- `{c}`")
        return "\n".join(out)
    return await _safe(run())


@tool()
async def thm_my_capability_score() -> str:
    """Your TryHackMe capability score and its components (foundation, activity, specialism...), with trends."""
    async def run():
        data = await client().get("/api/v2/capability-score/me", auth=True)
        return fmt.capability(((data or {}).get("capabilityScore")) or {})
    return await _safe(run())


@tool()
async def thm_my_weekly_missions() -> str:
    """This week's missions (rooms, questions, streak days): your progress vs. the targets."""
    async def run():
        d = await client().get("/api/v2/users/missions/weekly", auth=True) or {}
        prog, goal = d.get("progress") or {}, d.get("tasks") or {}
        out = [f"# Weekly missions ({str(d.get('weekStart', ''))[:10]} → {str(d.get('weekEnd', ''))[:10]})",
               f"Status: {d.get('status', '?')}"]
        names = {"completeRooms": "Rooms", "completeQuestions": "Questions", "streakDays": "Streak days"}
        for k, label in names.items():
            if k in goal:
                out.append(f"- {label}: {prog.get(k, 0)} / {goal[k]}")
        return "\n".join(out)
    return await _safe(run())


@tool()
async def thm_my_notifications(unread_only: bool = True, limit: int = 15) -> str:
    """Your TryHackMe notifications (read-only: this does not mark them as read)."""
    async def run():
        d = await client().get("/api/v2/notifications", auth=True) or {}
        items = [n for n in d.get("notifications") or [] if not (unread_only and n.get("read"))]
        out = [f"Unread: {d.get('unreadNotificationsCount', 0)}"]
        for n in items[: max(1, min(limit, 50))]:
            text = fmt.html_to_md(n.get("description")).replace("\n", " ")
            out.append(f"- {str(n.get('created', ''))[:10]} [{n.get('category', '')}] {text}")
        return "\n".join(out)
    return await _safe(run())


@tool()
async def thm_my_social(list_type: Literal["followers", "following", "counts"] = "counts", page: int = 1) -> str:
    """Your followers / people you follow on TryHackMe, with their points and streaks."""
    async def run():
        uid = await _my_id()
        if list_type == "counts":
            c = await client().get("/api/v2/follows/count", {"userId": uid}, auth=True) or {}
            return f"- Followers: {c.get('followersCount', 0)}\n- Following: {c.get('followeesCount', 0)}"
        ep = "/api/v2/follows/followers" if list_type == "followers" else "/api/v2/follows/followees"
        data = await client().get(ep, {"userId": uid, "page": max(1, page), "limit": 25}, auth=True)
        return fmt.paged_list(
            data or {},
            lambda u: f"- **{u.get('username')}** — {u.get('totalPoints')} pts, {u.get('completedRooms')} rooms, "
                      f"{u.get('streak')}-day streak"
                      + (" · mutual" if u.get("isFollowedByRequestingUser") and u.get("isFollowingRequestingUser") else ""),
        )
    return await _safe(run())


@tool()
async def thm_my_rooms(
    status: Literal["all", "in-progress", "completed"] = "all",
    search: str = "",
    page: int = 1,
    limit: int = 25,
) -> str:
    """Rooms you've joined, optionally only in-progress or completed ones."""
    async def run():
        params = {"searchText": search, "page": max(1, page), "limit": max(1, min(limit, 100))}
        if status != "all":
            # The API's own completion filter isn't reliable; fetch a big page and filter here.
            params["limit"] = 100
        data = dict(await client().get("/api/v2/rooms/my-rooms", params, auth=True) or {})
        if status != "all":
            want = status == "completed"
            data["docs"] = [r for r in data.get("docs") or [] if bool(r.get("userCompleted")) == want][:limit]
        return fmt.paged_list(
            data,
            lambda r: f"- {'✅' if r.get('userCompleted') else '⏳'} **{r.get('title')}** (`{r.get('code')}`, "
                      f"{r.get('difficulty')}, {r.get('type')})",
        )
    return await _safe(run())


# ---------------------------------------------------------------- write tools (THM_ALLOW_WRITES=1)

async def _resolve_room(room_code: str) -> tuple[dict, list[dict]]:
    """Room details (with internal code) and its tasks."""
    code = _code(room_code)
    details = await client().get("/api/v2/rooms/details", {"roomCode": code}, auth=True)
    tasks = await client().get("/api/v2/rooms/tasks", {"roomCode": code}, auth=True)
    return details or {}, tasks if isinstance(tasks, list) else []


async def _pick_machine(machine_id: str) -> dict:
    vms = await client().get("/api/v2/vms/running", auth=True) or []
    if machine_id:
        for v in vms:
            if v.get("id") == machine_id or _code(machine_id) in (v.get("roomCode"), v.get("roomTitle")):
                return v
        raise THMError(f"No running machine matches '{machine_id}'. Use thm_my_running_machines.")
    if len(vms) == 1:
        return vms[0]
    if not vms:
        raise THMError("You have no running machines.")
    raise THMError("You have several machines running; pass machine_id (see thm_my_running_machines).")


@write_tool()
async def thm_start_machine(room_code: str, task_no: int | None = None) -> str:
    """Start a room's target machine (VM). Changes your account: uses your machine quota.

    task_no: which task's machine to start; default is the first task that has one.
    The machine takes 1-3 minutes to boot; check thm_my_running_machines for its IP.
    """
    async def run():
        details, tasks = await _resolve_room(room_code)
        with_vm = [t for t in sorted(tasks, key=lambda t: t.get("taskNo", 0)) if t.get("uploadId")]
        if task_no is not None:
            with_vm = [t for t in with_vm if t.get("taskNo") == task_no]
        if not with_vm:
            raise THMError(f"Room '{_code(room_code)}' has no deployable machine"
                           + (f" in task {task_no}." if task_no is not None else "."))
        t = with_vm[0]
        await client().post("/api/v2/vms/start", {
            "roomCode": details.get("code") or _code(room_code),
            "vmId": t["uploadId"],
            "taskId": t["_id"],
            "source": "room",
        })
        return (f"Starting the machine for task {t.get('taskNo')} of '{details.get('title')}'. "
                "It usually boots in 1-3 minutes; thm_my_running_machines shows its IP.")
    return await _safe(run())


@write_tool()
async def thm_extend_machine(machine_id: str = "") -> str:
    """Add 1 hour to a running machine. machine_id is optional if only one is running."""
    async def run():
        v = await _pick_machine(machine_id)
        try:
            await client().post("/api/v2/vms/extend", {"id": v["id"]})
        except THMError as e:
            raise THMError(
                f"TryHackMe refused to extend this machine (expires {str(v.get('expires', ''))[:16]} UTC). "
                "Machines can usually only be extended when they're close to expiring. "
                f"Details: {e}"
            ) from e
        return f"Added 1 hour to {v.get('title') or v.get('roomTitle')}."
    return await _safe(run())


@write_tool(destructive=True)
async def thm_terminate_machine(machine_id: str = "") -> str:
    """Terminate a running machine. Anything on it is lost. machine_id optional if only one runs."""
    async def run():
        v = await _pick_machine(machine_id)
        await client().post("/api/v2/vms/terminate", {"id": v["id"]})
        return f"Terminated {v.get('title') or v.get('roomTitle')} (`{v['id']}`)."
    return await _safe(run())


@write_tool()
async def thm_vote_room(room_code: str, recommend: bool = True) -> str:
    """Recommend (upvote) a room, or take your recommendation back with recommend=False."""
    async def run():
        details, _ = await _resolve_room(room_code)
        code = details.get("code") or _code(room_code)
        await client().post("/api/v2/rooms/votes", {"roomCode": code, "vote": recommend})
        v = await client().get("/api/v2/rooms/votes", {"roomCode": code}, auth=True) or {}
        return f"{'Recommended' if recommend else 'Removed your recommendation for'} '{details.get('title')}'. Votes: {v.get('votes')}."
    return await _safe(run())


@write_tool()
async def thm_join_room(room_code: str) -> str:
    """Join a room so it shows in your rooms and tracks progress. (Experimental.)"""
    async def run():
        details, _ = await _resolve_room(room_code)
        await client().post("/api/v2/rooms/join", {"roomCode": details.get("code") or _code(room_code)})
        return f"Joined '{details.get('title')}'."
    return await _safe(run())


@write_tool(destructive=True)
async def thm_leave_room(room_code: str) -> str:
    """Leave a room. Your progress in it may be lost. (Experimental.)"""
    async def run():
        details, _ = await _resolve_room(room_code)
        await client().post("/api/v2/rooms/leave", {"roomCode": details.get("code") or _code(room_code)})
        return f"Left '{details.get('title')}'."
    return await _safe(run())


# ---------------------------------------------------------------- prompts

@mcp.prompt()
def study_room(room_code: str) -> str:
    """Study a TryHackMe room task by task, as a tutor."""
    return (
        f"Help me study the TryHackMe room `{room_code}`. First call thm_room_overview. Then, one "
        "task at a time, use thm_get_task to explain the concepts and commands in plain language, "
        "give a small example I can try, and ask me the task's questions. Don't reveal answers; "
        "give hints if I'm stuck, and only move on when I say so."
    )


@mcp.prompt()
def quiz_me(room_code: str) -> str:
    """Quiz yourself on a room you've already done."""
    return (
        f"Quiz me on the TryHackMe room `{room_code}`. Use thm_room_questions and thm_get_task to "
        "write 8 new questions that test understanding rather than the room's exact answers: mix "
        "multiple choice, 'what does this command do', and short scenario questions. Ask one at a "
        "time, wait for my answer, then explain."
    )


@mcp.prompt()
def weekly_plan(hours: int = 5) -> str:
    """Plan this week's TryHackMe study around your path and goals."""
    return (
        f"I have about {hours} hours for TryHackMe this week. Use thm_my_current_path, "
        "thm_my_next_rooms, thm_my_weekly_missions and thm_my_stats to build a day-by-day plan that "
        "finishes my weekly missions and moves my path forward. Keep it realistic."
    )


# ---------------------------------------------------------------- entry point

def main() -> None:
    parser = argparse.ArgumentParser(description="TryHackMe MCP server")
    parser.add_argument("--transport", choices=["stdio", "sse", "streamable-http"], default="stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if args.transport == "stdio":
        mcp.run("stdio")
    else:
        mcp.run(args.transport, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
