# TryHackMe web API reference (unofficial)

These endpoints were mapped on **2026-11-22** by watching the network requests that tryhackme.com makes in a logged-in browser. They are undocumented, unversioned beyond `/v2`, and may change at any time.

Base URL: `https://tryhackme.com`

All responses are JSON of the form:

```json
{ "status": "success", "data": ... }
```

Auth is the `connect.sid` session cookie. "Public" means the endpoint returned data with no cookie at the time of mapping.

## Endpoints used by this server

| Endpoint | Auth | Params | `data` shape | Tool |
|---|---|---|---|---|
| `GET /api/v2/hacktivities/extended-search` | public | `kind` (rooms/paths/modules/networks/all), `searchText`, `difficulty`, `order`, `roomType`, `userProgress`, `page`, `limit` | paginated `{docs[], totalDocs, page, totalPages, hasNextPage, nextPage}`; doc: `title, code, kind, description, difficulty, type, freeToUse, timeToComplete, tags[], skillTags[], toolTags[], subscriptionTier` | `thm_search` |
| `GET /api/v2/rooms/details` | public | `roomCode` | `code, title, description, difficulty, type, freeToUse, locked, users, creators[{username}], tags[], pathCodes[], published, imageURL, ...` | `thm_room_overview`, `thm_room_full` |
| `GET /api/v2/rooms/tasks` | public (premium rooms need auth) | `roomCode` | `[{taskNo, title, description (HTML), questions[{questionNo, question, hint, progress{correct, noAnswer, submission, attempts}}], taskVmRegions[]}]` | `thm_get_task`, `thm_room_full` |
| `GET /api/v2/paths/outline` | public | `pathCode` | `code, title, description, difficulty, paid, derivedTimeToComplete, modules[{title, summary, rooms[{code, title, timeToComplete, progressPercentage}]}]` | `thm_path_outline` |
| `GET /api/v2/public-profile` | public | `username` | `username, level, rank, topPercentage, totalPoints, completedRoomsNumber, badgesNumber, streak, largestStreak, leagueTier, country, userRole, capabilityScore{value,pov}, enrolledPath{code,title}, isPrivateProfile, about, social usernames` | `thm_public_profile` |
| `GET /api/v2/public-profile/completed-rooms` | public | `username, page, limit` | paginated; doc: `code, title, difficulty, type, timeToComplete` | `thm_profile_completed_rooms` |
| `GET /api/v2/public-profile/badges` | public | `username, page, limit` | paginated; doc: `name, title, description, rarityTier, rarityPercent` | `thm_profile_badges` |
| `GET /api/v2/certificates/public-list` | public | `username, page, limit, sort` | paginated; doc: `name, achieved, certId, url` | `thm_profile_certificates` |
| `GET /api/v2/public-profile/top-tools` | public | `username` | `{tools[{tagId, label, categoryLabel}], curatedTagIds[]}` | `thm_profile_skills` |
| `GET /api/v2/public-profile/yearly-activity` | public | `username, year` | `{yearlyActivity[{date, count, level}], totalCount}` | `thm_profile_skills` |
| `GET /api/v2/users/self` | **auth** | — | `{user{username, email, ...}}` (**contains PII; whitelisted**) | `thm_check_auth` |
| `GET /api/v2/users/statistics` | **auth** | — | `level, rank, topPercentage, totalPoints, completedRoomsNumber, completedModulesNumber, badgesNumber, streak` | `thm_my_stats` |
| `GET /api/v2/users/points` | **auth** | — | `totalPoints, monthlyPoints` | `thm_my_stats` |
| `GET /api/v2/weekly-leagues/statistics` | **auth** | `minimal=true` | `tier, position, endDate, leagueStatus, weeksInCurrentLeague` | `thm_my_stats` |
| `GET /api/v2/paths/current` | **auth** | — | `{path{code,title,difficulty}, progress}` | `thm_my_current_path` |
| `GET /api/v2/path/progress` | **auth** | — | `percentage, completedHours, totalPathHours, hoursPerWeek, estimatedCompletionDate` | `thm_my_current_path` |
| `GET /api/v2/hacktivities/search-progress` | **auth** | `roomCodes` (comma-separated) | `{roomProgress[{roomCode, progressPercentage}], moduleProgress[], pathProgress[]}` | `thm_my_room_progress` |
| `GET /api/v2/vms/running` | **auth** | — | see Write endpoints section | `thm_my_running_machines` |
| `GET /api/v2/users/missions/streak-progression` | **auth** | — | streak/mission object (returned raw) | `thm_my_streak` |
| `GET /api/v2/rooms/votes` | public | `roomCode` | `votes, userVote` | `thm_room_overview` |
| `GET /api/v2/leaderboards/general` | public (rank needs auth) | `period` (monthly/alltime), `country` (2-letter, optional) | `users[{username, country, level, points, monthlyPoints, roomsIn, banned}], currentUserRank` | `thm_leaderboard` |
| `GET /module/{code}` (HTML page) | public | — | page embeds schema.org JSON-LD `LearningResource` with `name, identifier, description, hasPart[{name, url}]` | `thm_module` |
| `GET /api/v2/paths/current-module` | **auth** | — | `[{code, title, type, progress, moduleId}]` | `thm_my_current_module` |
| `GET /api/v2/recommendations` | **auth** | `contentType=room, contentSubType=challenge, recMethod=embedding, surface=challenge-page-v2` | `recommendations[{value (room code), order, is_dismissed}]` | `thm_my_recommendations` |
| `GET /api/v2/recommendations/details/{roomCode}` | **auth** | — | `code, title, description, difficulty, timeToComplete, users` | `thm_my_recommendations` |
| `GET /api/v2/capability-score/me` | **auth** | — | `capabilityScore{rawScore, pov, components{baseline, foundation, activity, specialism, versatility, relevancy}, componentTrends{…{trend}}, history}` | `thm_my_capability_score` |
| `GET /api/v2/users/missions/weekly` | **auth** | — | `weekStart, weekEnd, status, tasks{completeRooms, completeQuestions, streakDays}, progress{…}` | `thm_my_weekly_missions` |
| `GET /api/v2/notifications` | **auth** | — | `unreadNotificationsCount, notifications[{description, read, category, created}]` | `thm_my_notifications` |
| `GET /api/v2/follows/count` | **auth** | `userId` | `followersCount, followeesCount` | `thm_my_social` |
| `GET /api/v2/follows/followers`, `/followees` | **auth** | `userId, page, limit` | paginated; doc: `username, totalPoints, streak, completedRooms, isFollowedByRequestingUser, isFollowingRequestingUser` | `thm_my_social` |

## Observed but not used (candidates for future tools)

Read endpoints seen on the dashboard, room, paths and profile pages:

- `/api/v2/badges`
- `/api/v2/glossary`
- `/api/v2/roadmaps/premium?order=gamified-path`
- `/api/v2/path/current`
- `/api/v2/path/planned-session`
- `/api/v2/public-profile/skills-matrix?username=&role=&segment=`
- `/api/v2/certification/exams?status=`
- `/api/v2/vpns/connection?networkId=`
- `/api/v2/hacktivities/live-classes/cached`

## Write endpoints (used only when `THM_ALLOW_WRITES=1`)

Every write first does `GET /api/v2/auth/csrf` → `{"data": {"token": "..."}}`, then sends the
`POST` with header `csrf-token: <token>` and a JSON body. Bodies below were captured from the
website on 2026-11-22 unless marked.

| Endpoint | Body | Notes | Tool |
|---|---|---|---|
| `POST /api/v2/vms/start` | `{"roomCode": <details.code>, "vmId": <task.uploadId>, "taskId": <task._id>, "source": "room"}` | `roomCode` is the room's **internal** code from `rooms/details`, not the URL slug | `thm_start_machine` |
| `POST /api/v2/vms/extend` | `{"id": <running instance id>}` | +1 hour | `thm_extend_machine` |
| `POST /api/v2/vms/terminate` | `{"id": <running instance id>}` | | `thm_terminate_machine` |
| `POST /api/v2/rooms/votes` | `{"roomCode": <details.code>, "vote": true \| false}` | `false` sets `userVote` to `-1`; there's no way back to `0` (never voted) | `thm_vote_room` |
| `POST /api/v2/rooms/join` | `{"roomCode": ...}` (+ optional `pathCode`, `pageReferrer`) | **Inferred from the site's JS, not captured** | `thm_join_room` |
| `POST /api/v2/rooms/leave` | `{"roomCode": ...}` | **Inferred, not captured** | `thm_leave_room` |

`GET /api/v2/vms/running` returns `[{id, title, roomCode, roomTitle, state, expires, created, region, taskNumber, isPersistent, remote{privateIP, remoteUrl, protocol, bootTime, ...}}]`.

`GET /api/v2/rooms/my-rooms?searchText=&isRoomCompleted=&page=&limit=` returns paginated `{code, title, type, difficulty, freeToUse, userCompleted}`.

### Seen in the site's code but intentionally not implemented

- `POST rooms/answer`: answer submission. Out of scope by design.
- `rooms/reset-progress`, `rooms/manage/*`, `vms/hibernate`, `vms/resume`, `path/clubs/*`
- Analytics: `client-insights`, `users/experiment-observations`, `rooms/set-active`

## Notes

- Module pages have no JSON API call; their room list comes from the JSON-LD in the HTML.
- Room pages are rendered on the server; the browser still calls `rooms/details` and `rooms/tasks` after load.
- `GET` requests need no CSRF token; writes do (see above).
- Room URL slugs can differ from the internal room code (e.g. `linuxfundamentalspart1` → a different `code` in `rooms/details`). Votes and machines use the internal code.
- Requests carried no special headers beyond the cookie.
