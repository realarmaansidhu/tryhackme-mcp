# Recipes

Practical ways to use the server. Copy the prompts as-is or adapt them.

## Study a room with a tutor

> Use the `study_room` prompt with `linuxfundamentalspart1`.

Or in your own words:

> Let's do `furthernmap` together. Explain one task at a time in plain English, show me the commands with what each flag does, then ask me that task's questions. Hints only, no answers. Wait for me before moving on.

**Why it works:** `thm_get_task` gives the AI the exact room text, so explanations match what TryHackMe teaches rather than generic web knowledge.

## Find your next room

> What should I study next? Show my next 5 rooms in my path, plus TryHackMe's recommendations, and pick the best one for a 1-hour session.

Uses `thm_my_next_rooms`, `thm_my_recommendations` and `thm_room_overview`.

## Plan your week

> Use the `weekly_plan` prompt with 6 hours.

> I have 45 minutes on weekdays and 2 hours on Saturday. Plan my TryHackMe week so I finish my weekly missions and move my path forward.

## Run a lab end to end

Needs `THM_ALLOW_WRITES=1`.

> Start the machine for `furthernmap`. When it's up, tell me its IP and give me the nmap commands for task 3 with that IP filled in.

> I'm done, terminate my machine.

The AI uses `thm_start_machine` → `thm_my_running_machines` (to get the IP after boot) → `thm_get_task` → `thm_terminate_machine`. You run the commands yourself, on the AttackBox or your VPN-connected machine.

## Revise for a cert or exam

> I'm revising for SAL1. Search modules on SOC fundamentals and log analysis, list their rooms, and quiz me on the ones I've completed.

> Use `thm_room_questions` on `furthernmap` and turn the questions into flashcards (question on the front, the concept to remember on the back). Don't include answers I haven't earned.

## Make study notes

> Export `linuxfundamentalspart1` with `thm_room_full` and turn it into a one-page cheat sheet: key concepts, commands, and gotchas.

## Track progress

> How am I doing on TryHackMe this month? Stats, streak, league position, and how far I am through my path.

> Which rooms have I started but not finished? Sort by how close I am.

Uses `thm_my_rooms(status="in-progress")` and `thm_my_room_progress`.

## Compare and compete

> Compare my profile with `tryhackme`'s.

> Show the Canadian monthly leaderboard and where I rank.

## Explore a path before committing

> Show me the SOC Level 1 path outline, total hours, and which modules are free.

## Tips

- **Paste links.** Any tryhackme.com room, path, module or profile URL works as an argument.
- **Ask for hints, not answers.** The server is built for learning, and the tutor prompts tell the AI to hold answers back.
- **Be gentle with the API.** These are TryHackMe's own website endpoints. A human pace is fine; don't script hundreds of calls.
