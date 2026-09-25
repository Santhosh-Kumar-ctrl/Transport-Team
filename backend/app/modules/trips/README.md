# trips: schedules and the driver workflow

> When buses run, and the driver's **start → arrive at stop → end** workflow.

| | |
|---|---|
| **Owner** | Team A, member 3 |
| **Backend** | `backend/app/modules/trips/` |
| **Frontend** | `frontend/lib/modules/trips/` |
| **Status** | P0 done |

## Concepts
- **Schedule**: recurring service: route + bus + driver + direction + departure time + weekdays.
- **Trip**: one run of a schedule on a service date. Generated from schedules (idempotent).
- **Trip stop event**: planned vs actual time at each stop, in the order the bus visits them.

### Stop times
Pickup: stop *i* at `departure + offset_i`. Drop (campus first, list reversed): stop *i* at
`departure + (campus_offset − offset_i)`. Sequence 1 is always the departure point.

### State machine
```
scheduled ──start──▶ in_progress ──end──▶ completed
    └──────cancel───────┴──────cancel────▶ cancelled
```
- **start**: assigned driver (or admin). Bus must be `active`; neither driver nor bus may have
  another trip in progress. Marks stop 1 as reached at the start time.
- **arrive** (`/stops/{sequence}/arrive`): records `arrived_at` + `delay_min`. Stops may be skipped,
  but you can't go back to an earlier stop once a later one is reached.
- **end**: marks the terminus reached (if not already) and completes the trip.

## Data model
| Table | Key columns |
|---|---|
| `trip_schedules` | `route_id`, `bus_id`, `driver_id`, `direction` (pickup/drop), `departure_time` (local), `days_of_week` int[] ISO 1–7, `is_active` |
| `trips` | `schedule_id`, `route_id`, `bus_id`, `driver_id`, `direction`, `service_date`, `scheduled_departure` (UTC), `status`, `started_at`, `ended_at`, `current_delay_min`, `cancel_reason`; unique (schedule, date) |
| `trip_stop_events` | `trip_id`, `route_stop_id` (SET NULL), `stop_id`, `stop_name` (snapshot), `sequence`, `scheduled_at`, `arrived_at`, `delay_min` |
| `bus_positions` | **stub for Team B** (GPS/simulation): `trip_id`, `bus_id`, `latitude`, `longitude`, `speed_kmph`, `recorded_at` |

## API
| Method | Path | Role | Purpose |
|---|---|---|---|
| GET / POST | `/schedules` | admin | list / create (`driver_id` optional: defaults to the bus's assigned driver, else 422 `driver_required`) |
| PATCH | `/schedules/{id}` | admin | change bus, driver, time, days, active |
| POST | `/trips/generate` `{service_date?}` | admin | create the day's trips (also runs automatically) |
| GET | `/trips?service_date&status&route_id&driver_id` | admin, security | trips with route/bus/driver/stops |
| GET | `/trips/mine?service_date` | driver | today's trips for the driver |
| GET | `/trips/{id}` | any | trip detail incl. `next_stop` |
| POST | `/trips/{id}/start` | driver (own), admin | start |
| POST | `/trips/{id}/stops/{sequence}/arrive` | driver (own), admin | check in at a stop |
| POST | `/trips/{id}/end` | driver (own), admin | finish |
| POST | `/trips/{id}/cancel` `{reason}` | admin | cancel |

**Simulation:** with `ALLOW_SIMULATION=true`, admins may pass `started_at` / `arrived_at` to
replay late arrivals in demos and tests. Drivers can't (403).

Error codes: `bad_trip_state`, `bus_unavailable`, `already_running`, `already_arrived`,
`out_of_order`, `route_incomplete`, `bus_retired`, `wrong_role`.

## Events
| Emits | Payload highlights |
|---|---|
| `TripsGenerated` | `service_date`, `created` |
| `TripStarted` | `trip_id, route_id, bus_id, driver_id, direction, scheduled_departure, started_at, delay_min` |
| `StopArrived` | `sequence, stop_id, stop_name, scheduled_at, arrived_at, delay_min, is_last` |
| `TripEnded` | `ended_at, final_delay_min, skipped_stops` |
| `TripCancelled` | `reason` |
| `ScheduleCreated`, `ScheduleUpdated` | ids |

| `BusRunsReassigned` | `bus_id, driver_id, schedule_ids, trip_ids` |

Consumers: delay_monitor (TripStarted, StopArrived), boarding (TripEnded → attendance),
notifications, dashboard (live refresh).

| Consumes | Why |
|---|---|
| `BusDriverAssigned` (master_data) | `reassign_bus_driver`: the bus's active schedules and not-yet-started trips (today onwards) move to the new driver. Running/finished trips keep theirs |

## Background job
`trip-generator` runs every `TRIP_GENERATION_INTERVAL_SECONDS` (15 min) and at startup, so
today's trips always exist, including after midnight.

## Public service API
`get_trip`, `list_trips`, `active_trips`, `driver_trips`, `trips_for_route_on`, `trip_detail(s)`,
`next_stop(trip)`, `stops_after(trip, seq)`, `route_seat_capacity(route_id)`.

## Frontend screens
| Screen | Role | File |
|---|---|---|
| Today's runs | driver | `frontend/lib/modules/trips/screens/driver_home_screen.dart` |
| Run trip (line + ARRIVED) | driver | `frontend/lib/modules/trips/screens/driver_run_screen.dart` |
| Schedules | admin | `frontend/lib/modules/trips/screens/admin_schedules_screen.dart` |

## How to test
```bash
cd backend && .venv/Scripts/python -m pytest app/modules/trips -q
```

## Extension notes (Team B)
- **GPS / simulation:** write to `bus_positions`, then publish e.g. `BusPositionUpdated`. Auto-arrival
  (geofence) can call `service.arrive_at_stop` so everything downstream keeps working.
- **Temporary route reassignment:** `PATCH /schedules/{id}` changes bus/driver for future trips.
  A one-day swap = new trip row with `schedule_id = NULL` (supported by the schema).
