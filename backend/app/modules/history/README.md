# history: operational history and reports

> Read-only views: the event timeline, per-trip reports and attendance reports (with CSV export).

| | |
|---|---|
| **Owner** | Team A, member 5 |
| **Backend** | `backend/app/modules/history/` |
| **Frontend** | `frontend/lib/modules/history/` |
| **Status** | P0 done |

## Source of truth
Every module publishes domain events. `core.events` stores each one in `domain_events`
(type, aggregate, actor, JSON payload, timestamp). History reads that log plus trips, boardings,
attendance and delay reports. **Owns no tables.** It reads other modules' tables for reporting
only (see CONTRIBUTING rule 1).

## API
| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | `/history/events?type=&type=&aggregate_type&aggregate_id&trip_id&route_id&date_from&date_to&limit&offset` | admin, security | filtered event log (newest first) with actor names |
| GET | `/history/trips/{id}/timeline` | admin, security | everything that happened on a trip, oldest first |
| GET | `/history/trips?date_from&date_to&route_id` | admin, security | per-trip report: times, max delay, alerts, boarded, present, absent |
| GET | `/history/attendance?date_from&date_to&route_id&student_id&format=json\|csv` | admin, security | attendance rows / CSV download |

## Frontend screens
| Screen | Role | File |
|---|---|---|
| Reports (trips, attendance, timeline) | admin | `frontend/lib/modules/history/screens/admin_history_screen.dart` |

## How to test
```bash
cd backend && .venv/Scripts/python -m pytest app/modules/history -q
```

## Extension notes (Team B)
`domain_events` is the input for route-utilisation analytics and demand prediction, and the
memory the agent uses to verify a resolution ("did a `TripDelayResolved` follow?").
