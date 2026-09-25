# trips: dev log

## 2026-09-24: Runs follow the bus's assigned driver
**Built**
- Subscriber on `BusDriverAssigned` → `reassign_bus_driver()` updates active schedules and today's
  and future `scheduled` trips of that bus, then publishes `BusRunsReassigned` (the dashboard
  forwards it so the new driver's Runs screen refreshes).
- `ScheduleIn.driver_id` is optional and defaults to the bus's driver.

**Decisions (and why)**
- Reacting to an event instead of master_data updating schedules directly keeps table ownership
  clean (see CONTRIBUTING rule 1).

## 2026-09-24: Flutter screens
**Built**
- Driver home (today's runs as big blocks with one action), run screen (dark board, line diagram
  with a green ARRIVED on the next stop only, End trip), admin Schedules (list + add dialog that
  also creates today's trip).

**Decisions (and why)**
- **One action per stop.** Only the next stop gets an ARRIVED button, so a driver can't tap the wrong row at a glance.
- **Dark board styling for driver screens** gives high contrast in a cab and matches the departure-board language.
- Starting a trip asks for confirmation, because it notifies every rider on the route.

## 2026-09-24: P0 trips module
**Built**
- Schedules, idempotent daily trip generation, start / arrive / end / cancel, trip detail with
  `next_stop`, background generator job, `bus_positions` telemetry stub.

**Decisions (and why)**
- **Stop times are planned when the trip is generated** (`trip_stop_events.scheduled_at`) rather than
  computed on the fly. Planned-vs-actual history stays correct even if the route is edited later,
  and the stop name is snapshotted for the same reason.
- **Drop trips reverse the route** and use `campus_offset − offset`, so admins maintain one stop list
  per route instead of two.
- **Starting a trip marks stop 1 as reached.** The bus leaves from there, so the first delay
  observation is the departure delay.
- **Skipping stops is allowed; going backwards isn't.** Real buses skip empty stops, and
  back-filling an earlier stop after a later one would corrupt delay maths.
- **Generation uses a savepoint per trip + unique (schedule_id, service_date)**, so concurrent
  generation (startup job + admin button) can't create duplicates.
- **Simulated timestamps are admin-only** behind `ALLOW_SIMULATION`. The Day-30 demo needs to
  "make the bus late" on demand, but drivers must never be able to fake times.
- `route_seat_capacity` lives here (min bus capacity across active schedules) because schedules
  are what tie buses to routes. Allocation calls it.

**Issues / next**
- Trips are generated for the college timezone's "today". A trip scheduled 23:50 that runs past
  midnight still belongs to its service date, which is intended.
- No ad-hoc trip endpoint yet (the schema supports `schedule_id = NULL`). Add it with temporary
  reassignment (P1).
