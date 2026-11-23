"""Turn TryHackMe API payloads into compact Markdown for the model."""

from __future__ import annotations

import json
import re
from typing import Any

from markdownify import markdownify

ROOM_URL = "https://tryhackme.com/room/{code}"
PATH_URL = "https://tryhackme.com/path/outline/{code}"
PROFILE_URL = "https://tryhackme.com/p/{username}"


def html_to_md(html: str | None) -> str:
    if not html:
        return ""
    md = markdownify(html, heading_style="ATX", bullets="-", code_language="")
    md = re.sub(r"(?m)^#{1,6}[ \t]*$\n?", "", md)   # empty headings left by spacer elements
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip()


def minutes(n: Any) -> str:
    try:
        n = int(n)
    except (TypeError, ValueError):
        return "?"
    return f"{n // 60}h {n % 60}m" if n >= 60 else f"{n} min"


def search_results(data: dict, kind: str) -> str:
    docs = data.get("docs") or []
    if not docs:
        return "No results."
    lines = [
        f"**{data.get('totalDocs', len(docs))} results** (page {data.get('page', 1)} of "
        f"{data.get('totalPages', 1)})\n"
    ]
    for d in docs:
        code = d.get("code", "")
        k = d.get("kind") or kind
        access = "free" if d.get("freeToUse") else "premium"
        bits = [b for b in (d.get("difficulty"), d.get("type"), access) if b]
        if d.get("timeToComplete"):
            bits.append(minutes(d["timeToComplete"]))
        lines.append(f"- **{d.get('title', code)}** (`{code}`, {k}) — {', '.join(bits)}")
        if d.get("description"):
            lines.append(f"  {d['description'].strip()}")
    if data.get("hasNextPage"):
        lines.append(f"\nMore results: page={data.get('nextPage')}")
    return "\n".join(lines)


def room_overview(d: dict, tasks: list[dict] | None, slug: str | None = None) -> str:
    internal = d.get("code", "")
    code = slug or internal
    creators = ", ".join(c.get("username", "") for c in d.get("creators") or [])
    out = [
        f"# {d.get('title', code)}",
        f"{(d.get('description') or '').strip()}\n",
        f"- Code: `{code}` · {ROOM_URL.format(code=code)}"
        + (f" (internal code `{internal}`)" if internal and internal != code else ""),
        f"- Difficulty: {d.get('difficulty', '?')} · Type: {d.get('type', '?')}",
        f"- Access: {'free' if d.get('freeToUse') else 'premium'}"
        + (" · locked" if d.get("locked") else ""),
    ]
    if creators:
        out.append(f"- Created by: {creators}")
    if d.get("users") is not None:
        out.append(f"- Joined by: {d['users']:,} users")
    if d.get("_votes") is not None:
        out.append(f"- Upvotes: {d['_votes']:,}")
    if d.get("tags"):
        out.append(f"- Tags: {', '.join(map(str, d['tags']))}")
    if d.get("pathCodes"):
        out.append(f"- In paths: {', '.join(d['pathCodes'])}")
    if tasks:
        out.append("\n## Tasks")
        for t in tasks:
            q = len(t.get("questions") or [])
            done = sum(1 for x in t.get("questions") or [] if (x.get("progress") or {}).get("correct"))
            prog = f", {done}/{q} answered" if q and done else ""
            out.append(f"{t.get('taskNo')}. {t.get('title')} ({q} questions{prog})")
    return "\n".join(out)


def task_md(t: dict, *, include_hints: bool = True, include_my_answers: bool = False) -> str:
    out = [f"## Task {t.get('taskNo')}: {t.get('title', '')}", "", html_to_md(t.get("description"))]
    qs = t.get("questions") or []
    if qs:
        out += ["", "### Questions"]
        for q in qs:
            p = q.get("progress") or {}
            status = " ✅" if p.get("correct") else ""
            text = html_to_md(q.get("question")) or "(no question text)"
            out.append(f"{q.get('questionNo')}. {text}{status}")
            if include_hints and q.get("hint"):
                out.append(f"   - Hint: {q['hint'].strip()}")
            if p.get("noAnswer"):
                out.append("   - (no answer needed)")
            if include_my_answers and p.get("submission"):
                out.append(f"   - Your submitted answer: `{p['submission']}`")
    return "\n".join(out).strip()


def path_outline(d: dict, progress: dict[str, int] | None = None) -> str:
    code = d.get("code", "")
    out = [
        f"# {d.get('title', code)}",
        f"{(d.get('description') or '').strip()}\n",
        f"- Code: `{code}` · {PATH_URL.format(code=code)}",
        f"- Difficulty: {d.get('difficulty', '?')} · Paid: {bool(d.get('paid'))}",
    ]
    if d.get("derivedTimeToComplete"):
        out.append(f"- Estimated time: {minutes(d['derivedTimeToComplete'])}")
    for i, m in enumerate(d.get("modules") or [], 1):
        out.append(f"\n## Module {i}: {m.get('title', '')}")
        if m.get("summary"):
            out.append(m["summary"].strip())
        for r in m.get("rooms") or []:
            pct = r.get("progressPercentage")
            if progress and r.get("code") in progress:
                pct = progress[r["code"]]
            mark = f" — {pct}%" if pct else ""
            out.append(f"- {r.get('title')} (`{r.get('code')}`, {minutes(r.get('timeToComplete'))}){mark}")
    return "\n".join(out)


def public_profile(d: dict) -> str:
    u = d.get("username", "")
    out = [f"# {u}", f"{PROFILE_URL.format(username=u)}\n"]
    if d.get("isPrivateProfile"):
        out.append("_This profile is private; only basic fields are shown._\n")
    fields = [
        ("Level", d.get("level")),
        ("Rank", d.get("rank")),
        ("Top", f"{d['topPercentage']}%" if d.get("topPercentage") is not None else None),
        ("Points", d.get("totalPoints")),
        ("Rooms completed", d.get("completedRoomsNumber")),
        ("Badges", d.get("badgesNumber")),
        ("Streak", d.get("streak")),
        ("Longest streak", d.get("largestStreak")),
        ("League", d.get("leagueTier")),
        ("Country", d.get("country")),
        ("Role", d.get("userRole")),
    ]
    out += [f"- {k}: {v}" for k, v in fields if v not in (None, "")]
    cs = d.get("capabilityScore") or {}
    if cs.get("value") is not None:
        out.append(f"- Capability score: {cs['value']}" + (f" ({cs['pov']})" if cs.get("pov") else ""))
    ep = d.get("enrolledPath") or {}
    if ep.get("title"):
        out.append(f"- Current path: {ep['title']} (`{ep.get('code')}`)")
    if d.get("about"):
        out.append(f"\n{d['about'].strip()}")
    links = {
        "GitHub": d.get("githubUsername"),
        "LinkedIn": d.get("linkedInUsername"),
        "X": d.get("twitterUsername"),
        "Website": d.get("personalWebsite"),
    }
    links = {k: v for k, v in links.items() if v}
    if links:
        out.append("\n" + " · ".join(f"{k}: {v}" for k, v in links.items()))
    return "\n".join(out)


# Fields of /users/self that are safe to show. Everything else (email, phone,
# Discord token, demographics, subscription ids...) is dropped on purpose.
SAFE_SELF_FIELDS = (
    "username", "isPremium", "accountType", "dateSignUp", "verified", "roles",
)


def safe_self(user: dict) -> dict:
    out = {k: user.get(k) for k in SAFE_SELF_FIELDS if k in user}
    tfa = (user.get("twoFactorAuth") or {}).get("isTwoFactorEnabled")
    if tfa is not None:
        out["twoFactorEnabled"] = tfa
    return out


def paged_list(data: dict, render) -> str:
    docs = data.get("docs") or []
    if not docs:
        return "Nothing here."
    lines = [render(d) for d in docs]
    foot = f"\n(page {data.get('page', 1)} of {data.get('totalPages', 1)}, {data.get('totalDocs', len(docs))} total)"
    return "\n".join(lines) + foot


# ---------------------------------------------------------------- modules (JSON-LD in page HTML)

_LD_RE = re.compile(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', re.S)


def module_from_html(html: str, code: str) -> dict | None:
    """Module pages embed a schema.org LearningResource whose hasPart lists the rooms."""
    for raw in _LD_RE.findall(html or ""):
        try:
            data = json.loads(raw)
        except ValueError:
            continue
        nodes = data.get("@graph", [data]) if isinstance(data, dict) else data
        for n in nodes if isinstance(nodes, list) else []:
            if isinstance(n, dict) and n.get("@type") == "LearningResource" and n.get("hasPart"):
                rooms = []
                for part in n["hasPart"]:
                    url = part.get("url", "")
                    rooms.append({"title": part.get("name"), "code": url.rstrip("/").rsplit("/", 1)[-1]})
                return {"code": n.get("identifier") or code, "title": n.get("name"),
                        "description": n.get("description"), "rooms": rooms}
    return None


def module_md(m: dict) -> str:
    out = [f"# {m.get('title')}", (m.get("description") or "").strip(),
           f"\n- Code: `{m.get('code')}` · https://tryhackme.com/module/{m.get('code')}", "\n## Rooms"]
    out += [f"{i}. {r['title']} (`{r['code']}`)" for i, r in enumerate(m.get("rooms") or [], 1)]
    return "\n".join(out)


# ---------------------------------------------------------------- leaderboard / compare / capability

def leaderboard(d: dict, period: str, country: str, limit: int) -> str:
    users = [u for u in d.get("users") or [] if not u.get("banned")][:limit]
    where = country.upper() if country else "worldwide"
    pts_key = "monthlyPoints" if period == "monthly" else "points"
    out = [f"# Leaderboard: {period}, {where}"]
    if d.get("currentUserRank") not in (None, "", "-"):
        out.append(f"Your rank on this board: {d['currentUserRank']}\n")
    out.append("| # | User | Points | Rooms | Level | Country |\n|---|---|---|---|---|---|")
    for i, u in enumerate(users, 1):
        out.append(f"| {i} | {u.get('username')} | {u.get(pts_key, u.get('points'))} | {u.get('roomsIn')} | "
                   f"{u.get('level')} | {(u.get('country') or '').upper()} |")
    return "\n".join(out)


def compare(a: dict, b: dict) -> str:
    rows = [("Level", "level"), ("Rank", "rank"), ("Top %", "topPercentage"), ("Points", "totalPoints"),
            ("Rooms completed", "completedRoomsNumber"), ("Badges", "badgesNumber"), ("Streak", "streak"),
            ("Longest streak", "largestStreak"), ("League", "leagueTier")]
    out = [f"| | {a.get('username')} | {b.get('username')} |", "|---|---|---|"]
    for label, k in rows:
        out.append(f"| {label} | {a.get(k, '—')} | {b.get(k, '—')} |")
    ca, cb = (a.get("capabilityScore") or {}).get("value"), (b.get("capabilityScore") or {}).get("value")
    out.append(f"| Capability score | {ca if ca is not None else '—'} | {cb if cb is not None else '—'} |")
    pa, pb = (a.get("enrolledPath") or {}).get("title"), (b.get("enrolledPath") or {}).get("title")
    out.append(f"| Current path | {pa or '—'} | {pb or '—'} |")
    return "\n".join(out)


def capability(c: dict) -> str:
    if not c:
        return "No capability score yet."
    out = [f"# Capability score: {c.get('rawScore')}" + (f" ({c['pov']})" if c.get("pov") else "")]
    trends = c.get("componentTrends") or {}
    for k, v in (c.get("components") or {}).items():
        t = trends.get(k) or {}
        arrow = {"up": " ↑", "down": " ↓"}.get(str(t.get("trend", "")).lower(), "")
        out.append(f"- {k.capitalize()}: {v}{arrow}")
    return "\n".join(out)


def machine(v: dict) -> str:
    remote = v.get("remote") or {}
    ip = remote.get("privateIP") or "booting"
    exp = str(v.get("expires") or "")[:16].replace("T", " ")
    return (f"- **{v.get('title') or 'machine'}** · room: {v.get('roomTitle') or v.get('roomCode')} · "
            f"state: {v.get('state', '?')} · IP: {ip}" + (f" · expires {exp} UTC" if exp else "")
            + f" · id `{v.get('id')}`")
