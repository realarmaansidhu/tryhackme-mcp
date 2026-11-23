"""Offline tests: every TryHackMe call is mocked with payloads shaped like the real API."""

import httpx
import pytest
import respx

from tryhackme_mcp import server
from tryhackme_mcp.client import THMClient
from tryhackme_mcp.formatting import safe_self

BASE = "https://tryhackme.com"

DETAILS = {
    "code": "linuxfundamentalspart1",
    "title": "Linux Fundamentals (Pt1)",
    "description": "Embark on the journey of learning the fundamentals of Linux.",
    "difficulty": "easy",
    "type": "walkthrough",
    "freeToUse": True,
    "locked": False,
    "users": 1321669,
    "creators": [{"username": "tryhackme"}],
    "tags": [],
    "pathCodes": ["presecurity"],
}
TASKS = [
    {
        "taskNo": 2,
        "title": "Talking to Linux",
        "description": "<h2>Who are you?</h2><p>Run <code>whoami</code>.</p><pre><code>whoami</code></pre>",
        "questions": [
            {"questionNo": 1, "question": "<p>What user are you?</p>", "hint": "use whoami",
             "progress": {"correct": True, "submission": "tryhackme", "noAnswer": False}},
        ],
    },
    {
        "taskNo": 1,
        "title": "Introduction",
        "description": "<p>Linux is everywhere.</p>",
        "questions": [{"questionNo": 1, "question": "Read me", "hint": "",
                       "progress": {"noAnswer": True}}],
    },
]
SEARCH = {
    "docs": [{"title": "Nmap", "code": "furthernmap", "kind": "rooms", "difficulty": "easy",
              "type": "walkthrough", "freeToUse": True, "timeToComplete": 90,
              "description": "Learn nmap."}],
    "totalDocs": 30, "page": 1, "totalPages": 3, "hasNextPage": True, "nextPage": 2,
}


def ok(data):
    return httpx.Response(200, json={"status": "success", "data": data})


@pytest.fixture(autouse=True)
def fresh_client(monkeypatch):
    monkeypatch.delenv("THM_SESSION", raising=False)
    monkeypatch.delenv("THM_COOKIE", raising=False)
    server.set_client(None)
    yield
    server.set_client(None)


@respx.mock
async def test_search():
    route = respx.get(f"{BASE}/api/v2/hacktivities/extended-search").mock(return_value=ok(SEARCH))
    out = await server.thm_search("nmap")
    assert "**Nmap** (`furthernmap`" in out and "1h 30m" in out and "page=2" in out
    assert route.calls[0].request.url.params["searchText"] == "nmap"


@respx.mock
async def test_room_overview_sorts_tasks_and_accepts_url():
    respx.get(f"{BASE}/api/v2/rooms/details").mock(return_value=ok(DETAILS))
    respx.get(f"{BASE}/api/v2/rooms/tasks").mock(return_value=ok(TASKS))
    out = await server.thm_room_overview("https://tryhackme.com/room/linuxfundamentalspart1")
    assert "# Linux Fundamentals (Pt1)" in out
    assert "1,321,669" in out
    assert "2. Talking to Linux (1 questions, 1/1 answered)" in out


@respx.mock
async def test_get_task_markdown_hints_and_answers():
    respx.get(f"{BASE}/api/v2/rooms/tasks").mock(return_value=ok(TASKS))
    out = await server.thm_get_task("linuxfundamentalspart1", 2)
    assert "## Task 2: Talking to Linux" in out
    assert "## Who are you?" in out and "whoami" in out
    assert "Hint: use whoami" in out and "✅" in out
    assert "tryhackme`" not in out  # own answers hidden by default
    out2 = await server.thm_get_task("linuxfundamentalspart1", 2, include_my_answers=True)
    assert "Your submitted answer: `tryhackme`" in out2


@respx.mock
async def test_get_task_missing():
    respx.get(f"{BASE}/api/v2/rooms/tasks").mock(return_value=ok(TASKS))
    out = await server.thm_get_task("linuxfundamentalspart1", 9)
    assert out.startswith("Error:") and "Tasks: 1, 2" in out


@respx.mock
async def test_room_full_orders_tasks():
    respx.get(f"{BASE}/api/v2/rooms/details").mock(return_value=ok(DETAILS))
    respx.get(f"{BASE}/api/v2/rooms/tasks").mock(return_value=ok(TASKS))
    out = await server.thm_room_full("linuxfundamentalspart1")
    assert out.index("Task 1: Introduction") < out.index("Task 2: Talking to Linux")


@respx.mock
async def test_empty_tasks_gives_helpful_error():
    respx.get(f"{BASE}/api/v2/rooms/tasks").mock(return_value=ok([]))
    out = await server.thm_get_task("someviproom", 1)
    assert "premium" in out


@respx.mock
async def test_path_outline():
    respx.get(f"{BASE}/api/v2/paths/outline").mock(return_value=ok({
        "code": "jrpenetrationtester", "title": "Jr Penetration Tester", "difficulty": "easy",
        "derivedTimeToComplete": 3360,
        "modules": [{"title": "Network Security", "summary": "Scan stuff.",
                     "rooms": [{"title": "Nmap", "code": "furthernmap", "timeToComplete": 90,
                                "progressPercentage": 100}]}],
    }))
    out = await server.thm_path_outline("jrpenetrationtester")
    assert "## Module 1: Network Security" in out and "`furthernmap`" in out and "100%" in out


@respx.mock
async def test_public_profile():
    respx.get(f"{BASE}/api/v2/public-profile").mock(return_value=ok({
        "username": "alice", "level": 12, "rank": 999, "topPercentage": 1, "totalPoints": 5000,
        "completedRoomsNumber": 200, "capabilityScore": {"value": 54, "pov": "red"},
        "enrolledPath": {"title": "SOC Level 1", "code": "soclevel1"}, "isPrivateProfile": False,
    }))
    out = await server.thm_public_profile("https://tryhackme.com/p/alice")
    assert "# alice" in out and "Capability score: 54 (red)" in out and "SOC Level 1" in out


async def test_my_tools_require_login():
    out = await server.thm_my_stats()
    assert out.startswith("Error:") and "THM_SESSION" in out
    assert "Not logged in" in await server.thm_check_auth()


@respx.mock
async def test_cookie_is_sent_and_self_is_whitelisted(monkeypatch):
    monkeypatch.setenv("THM_SESSION", "s%3Aabc")
    route = respx.get(f"{BASE}/api/v2/users/self").mock(return_value=ok({"user": {
        "username": "alice", "email": "alice@example.com", "isPremium": True,
        "discordToken": "SECRET", "demographics": {"phoneNumber": "555"},
        "twoFactorAuth": {"isTwoFactorEnabled": True},
    }}))
    out = await server.thm_check_auth()
    assert route.calls[0].request.headers["cookie"] == "connect.sid=s%3Aabc"
    assert "alice" in out and "twoFactorEnabled" in out
    for secret in ("alice@example.com", "SECRET", "555"):
        assert secret not in out


@respx.mock
async def test_401_and_bot_wall(monkeypatch):
    monkeypatch.setenv("THM_SESSION", "x")
    respx.get(f"{BASE}/api/v2/users/statistics").mock(return_value=httpx.Response(401, json={}))
    respx.get(f"{BASE}/api/v2/users/points").mock(return_value=ok({}))
    respx.get(f"{BASE}/api/v2/weekly-leagues/statistics").mock(return_value=ok({}))
    assert "expired" in await server.thm_my_stats()

    respx.get(f"{BASE}/api/v2/rooms/tasks").mock(
        return_value=httpx.Response(403, headers={"content-type": "text/html", "x-vercel-mitigated": "challenge"})
    )
    assert "bot protection" in await server.thm_get_task("x", 1)


@respx.mock
async def test_room_progress(monkeypatch):
    monkeypatch.setenv("THM_SESSION", "x")
    route = respx.get(f"{BASE}/api/v2/hacktivities/search-progress").mock(return_value=ok({
        "roomProgress": [{"roomCode": "furthernmap", "progressPercentage": 100}]}))
    out = await server.thm_my_room_progress(["furthernmap", "https://tryhackme.com/room/nmap01"])
    assert route.calls[0].request.url.params["roomCodes"] == "furthernmap,nmap01"
    assert "`furthernmap`: 100%" in out and "`nmap01`: 0%" in out


def test_safe_self_drops_everything_unknown():
    assert set(safe_self({"username": "a", "email": "e", "zzz": 1})) == {"username"}


async def test_all_tools_registered():
    tools = await server.mcp.list_tools()
    names = {t.name for t in tools}
    assert {"thm_search", "thm_get_task", "thm_room_full", "thm_my_stats"} <= names
    assert len(names) == 28
    assert not any(t.annotations.destructive_hint for t in tools)
    assert all(t.annotations and t.annotations.read_only_hint for t in tools)


MODULE_HTML = """<html><head>
<script type="application/ld+json">{"@context":"https://schema.org","@type":"LearningResource",
"name":"Linux Fundamentals","identifier":"linux-fundamentals","description":"Get comfortable with Linux.",
"hasPart":[{"@type":"LearningResource","name":"Linux Fundamentals Part 1","url":"https://tryhackme.com/room/linuxfundamentalspart1"},
{"@type":"LearningResource","name":"Linux Fundamentals Part 2","url":"https://tryhackme.com/room/linuxfundamentalspart2"}]}</script>
</head><body></body></html>"""


@respx.mock
async def test_module_from_json_ld():
    respx.get(f"{BASE}/module/linux-fundamentals").mock(
        return_value=httpx.Response(200, text=MODULE_HTML, headers={"content-type": "text/html"}))
    out = await server.thm_module("https://tryhackme.com/module/linux-fundamentals")
    assert "# Linux Fundamentals" in out
    assert "1. Linux Fundamentals Part 1 (`linuxfundamentalspart1`)" in out
    assert "2. Linux Fundamentals Part 2 (`linuxfundamentalspart2`)" in out


@respx.mock
async def test_overview_votes_use_internal_code():
    respx.get(f"{BASE}/api/v2/rooms/details").mock(return_value=ok({**DETAILS, "code": "linuxinternal"}))
    respx.get(f"{BASE}/api/v2/rooms/tasks").mock(return_value=ok(TASKS))
    route = respx.get(f"{BASE}/api/v2/rooms/votes").mock(return_value=ok({"votes": 874, "userVote": 0}))
    assert "Upvotes: 874" in await server.thm_room_overview("linuxfundamentalspart1")
    assert route.calls[0].request.url.params["roomCode"] == "linuxinternal"


@respx.mock
async def test_room_questions_skips_no_answer():
    respx.get(f"{BASE}/api/v2/rooms/tasks").mock(return_value=ok(TASKS))
    out = await server.thm_room_questions("linuxfundamentalspart1")
    assert "What user are you?" in out and "Read me" not in out and "tryhackme`" not in out


@respx.mock
async def test_leaderboard_hides_banned_and_uses_monthly_points():
    route = respx.get(f"{BASE}/api/v2/leaderboards/general").mock(return_value=ok({
        "users": [{"username": "cheater", "banned": True, "points": 9, "monthlyPoints": 9},
                  {"username": "alice", "banned": False, "points": 100, "monthlyPoints": 42, "roomsIn": 5,
                   "level": 7, "country": "ca"}],
        "currentUserRank": 120}))
    out = await server.thm_leaderboard("monthly", "CA")
    assert route.calls[0].request.url.params["country"] == "ca"
    assert "cheater" not in out and "| 1 | alice | 42 |" in out and "Your rank on this board: 120" in out


@respx.mock
async def test_next_rooms(monkeypatch):
    monkeypatch.setenv("THM_SESSION", "x")
    respx.get(f"{BASE}/api/v2/paths/current").mock(return_value=ok(
        {"path": {"code": "jrpenetrationtester", "title": "Jr Pen Tester"}, "progress": 40}))
    respx.get(f"{BASE}/api/v2/paths/outline").mock(return_value=ok({"modules": [
        {"title": "Net", "rooms": [{"title": "Done", "code": "done", "progressPercentage": 100},
                                   {"title": "Half", "code": "half", "progressPercentage": 50, "timeToComplete": 30},
                                   {"title": "New", "code": "new", "progressPercentage": 0}]}]}))
    out = await server.thm_my_next_rooms(limit=5)
    assert "`done`" not in out and out.index("`half`") < out.index("`new`") and "50% started" in out


@respx.mock
async def test_recommendations(monkeypatch):
    monkeypatch.setenv("THM_SESSION", "x")
    respx.get(f"{BASE}/api/v2/recommendations").mock(return_value=ok({"recommendations": [
        {"value": "b", "order": 2}, {"value": "a", "order": 1}, {"value": "z", "order": 0, "is_dismissed": True}]}))
    respx.get(f"{BASE}/api/v2/recommendations/details/a").mock(return_value=ok(
        {"title": "Room A", "difficulty": "easy", "timeToComplete": 45}))
    respx.get(f"{BASE}/api/v2/recommendations/details/b").mock(return_value=ok(
        {"title": "Room B", "difficulty": "hard", "timeToComplete": 120}))
    out = await server.thm_my_recommendations()
    assert out.index("Room A") < out.index("Room B") and "`z`" not in out and "2h 0m" in out


@respx.mock
async def test_social_uses_my_id(monkeypatch):
    monkeypatch.setenv("THM_SESSION", "x")
    respx.get(f"{BASE}/api/v2/users/self").mock(return_value=ok({"user": {"_id": "u123"}}))
    route = respx.get(f"{BASE}/api/v2/follows/count").mock(return_value=ok(
        {"followersCount": 3, "followeesCount": 4}))
    out = await server.thm_my_social("counts")
    assert route.calls[0].request.url.params["userId"] == "u123" and "Followers: 3" in out


@respx.mock
async def test_compare_and_capability(monkeypatch):
    respx.get(f"{BASE}/api/v2/public-profile", params={"username": "a"}).mock(return_value=ok(
        {"username": "a", "level": 5, "capabilityScore": {"value": 10}}))
    respx.get(f"{BASE}/api/v2/public-profile", params={"username": "b"}).mock(return_value=ok(
        {"username": "b", "level": 9}))
    out = await server.thm_compare_profiles("a", "b")
    assert "| Level | 5 | 9 |" in out and "| Capability score | 10 | — |" in out

    monkeypatch.setenv("THM_SESSION", "x")
    respx.get(f"{BASE}/api/v2/capability-score/me").mock(return_value=ok({"capabilityScore": {
        "rawScore": 54, "pov": "red", "components": {"foundation": 20, "activity": 8},
        "componentTrends": {"activity": {"trend": "up"}}}}))
    out = await server.thm_my_capability_score()
    assert "Capability score: 54 (red)" in out and "Activity: 8 ↑" in out


async def test_prompts_registered():
    names = {p.name for p in await server.mcp.list_prompts()}
    assert names == {"study_room", "quiz_me", "weekly_plan"}


# ---------------------------------------------------------------- write tools

import importlib
import json as _json


@pytest.fixture
def writes(monkeypatch):
    monkeypatch.setenv("THM_SESSION", "s%3Aabc")
    monkeypatch.setenv("THM_ALLOW_WRITES", "1")
    mod = importlib.reload(server)
    mod.set_client(None)
    yield mod
    monkeypatch.delenv("THM_ALLOW_WRITES")
    importlib.reload(server)


def csrf():
    return respx.get(f"{BASE}/api/v2/auth/csrf").mock(return_value=ok({"token": "tok123"}))


async def test_write_tools_hidden_by_default():
    names = {t.name for t in await server.mcp.list_tools()}
    assert "thm_start_machine" not in names and "thm_terminate_machine" not in names


async def test_write_tools_registered_when_enabled(writes):
    tools = {t.name: t for t in await writes.mcp.list_tools()}
    assert len(tools) == 34
    assert tools["thm_terminate_machine"].annotations.destructive_hint
    assert not tools["thm_start_machine"].annotations.read_only_hint


@respx.mock
async def test_start_machine_body_and_csrf(writes):
    csrf()
    respx.get(f"{BASE}/api/v2/rooms/details").mock(return_value=ok({**DETAILS, "code": "linuxinternal"}))
    respx.get(f"{BASE}/api/v2/rooms/tasks").mock(return_value=ok([
        {"taskNo": 2, "_id": "t2", "uploadId": "vm2", "title": "b"},
        {"taskNo": 1, "_id": "t1", "uploadId": "vm1", "title": "a"},
        {"taskNo": 3, "_id": "t3", "title": "no vm"},
    ]))
    start = respx.post(f"{BASE}/api/v2/vms/start").mock(return_value=ok({}))
    out = await writes.thm_start_machine("https://tryhackme.com/room/linuxfundamentalspart1")
    req = start.calls[0].request
    assert req.headers["csrf-token"] == "tok123"
    assert "connect.sid=s%3Aabc" in req.headers["cookie"]
    assert _json.loads(req.content) == {"roomCode": "linuxinternal", "vmId": "vm1", "taskId": "t1", "source": "room"}
    assert "task 1" in out
    assert "no deployable machine in task 3" in await writes.thm_start_machine("x", task_no=3)


@respx.mock
async def test_extend_and_terminate_pick_single_machine(writes):
    csrf()
    respx.get(f"{BASE}/api/v2/vms/running").mock(return_value=ok([{"id": "inst1", "title": "Linux", "roomCode": "r"}]))
    ext = respx.post(f"{BASE}/api/v2/vms/extend").mock(return_value=ok({}))
    term = respx.post(f"{BASE}/api/v2/vms/terminate").mock(return_value=ok({}))
    assert "Added 1 hour" in await writes.thm_extend_machine()
    ext.mock(return_value=httpx.Response(200, json={"status": "fail"}))
    assert "close to expiring" in await writes.thm_extend_machine()
    assert "Terminated" in await writes.thm_terminate_machine()
    assert _json.loads(ext.calls[0].request.content) == {"id": "inst1"}
    assert _json.loads(term.calls[0].request.content) == {"id": "inst1"}


@respx.mock
async def test_several_machines_need_an_id(writes):
    respx.get(f"{BASE}/api/v2/vms/running").mock(return_value=ok([{"id": "a"}, {"id": "b"}]))
    assert "pass machine_id" in await writes.thm_terminate_machine()


@respx.mock
async def test_vote_uses_internal_code(writes):
    csrf()
    respx.get(f"{BASE}/api/v2/rooms/details").mock(return_value=ok({**DETAILS, "code": "linuxinternal"}))
    respx.get(f"{BASE}/api/v2/rooms/tasks").mock(return_value=ok(TASKS))
    vote = respx.post(f"{BASE}/api/v2/rooms/votes").mock(return_value=ok({}))
    respx.get(f"{BASE}/api/v2/rooms/votes").mock(return_value=ok({"votes": 899}))
    out = await writes.thm_vote_room("linuxfundamentalspart1", recommend=True)
    assert _json.loads(vote.calls[0].request.content) == {"roomCode": "linuxinternal", "vote": True}
    assert "Votes: 899" in out


@respx.mock
async def test_post_refuses_without_switch(monkeypatch):
    monkeypatch.setenv("THM_SESSION", "x")
    from tryhackme_mcp.client import THMClient, THMError
    with pytest.raises(THMError, match="THM_ALLOW_WRITES"):
        await THMClient().post("/api/v2/vms/terminate", {"id": "x"})


def test_placeholder_cookie_is_not_a_login(monkeypatch):
    from tryhackme_mcp.client import is_authenticated
    monkeypatch.setenv("THM_SESSION", "your_connect_sid_here")
    assert not is_authenticated()


@respx.mock
async def test_my_rooms_filter(monkeypatch):
    monkeypatch.setenv("THM_SESSION", "x")
    respx.get(f"{BASE}/api/v2/rooms/my-rooms").mock(return_value=ok({"docs": [
        {"title": "Nmap", "code": "furthernmap", "userCompleted": True, "difficulty": "easy", "type": "walkthrough"},
        {"title": "Mr Robot", "code": "mrrobot", "userCompleted": False, "difficulty": "medium", "type": "challenge"}],
        "page": 1, "totalPages": 1, "totalDocs": 2}))
    out = await server.thm_my_rooms("in-progress")
    assert "Mr Robot" in out and "Nmap" not in out
    out = await server.thm_my_rooms("completed")
    assert "✅ **Nmap**" in out and "Mr Robot" not in out


def test_empty_headings_removed_and_slug_link():
    from tryhackme_mcp.formatting import html_to_md, room_overview
    assert "##" not in html_to_md("<h2> </h2><p>hi</p>").replace("## hi", "")
    out = room_overview({"code": "internal1", "title": "T"}, None, slug="nicename")
    assert "tryhackme.com/room/nicename" in out and "internal code `internal1`" in out
