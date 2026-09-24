# history: dev log

## 2026-09-24: Flutter screens
**Built**
- Reports screen: day stepper, Trips tab (route, time, driver, boarded/present/missed, on-time plate)
  and Attendance tab.

**Issues / next**
- CSV download button not in the UI yet (API supports `?format=csv`). Needs a web-download helper.

## 2026-09-24: P0 history module
**Built**
- Event log query API with filters, trip timeline, trip reports, attendance report + CSV.

**Decisions (and why)**
- **Event-sourced timeline, not per-module audit tables.** Every module already publishes events,
  and persisting them centrally gives a complete, uniformly shaped history for free.
- **`trip_id` filter matches the aggregate *or* `payload->>'trip_id'`**, because some trip-related
  events (e.g. capacity) are aggregated elsewhere but still belong on the trip's timeline.
- **Date filters use college-local day boundaries**, so "24 Sep" means the college's day, not UTC's.
- CSV shows local `HH:MM` for boarding time because that's what transport staff paste into
  spreadsheets.

**Issues / next**
- `domain_events.payload` JSON filters aren't indexed. Add a GIN index or a `trip_id` column
  if the table grows past a few hundred thousand rows.
