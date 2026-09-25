"""Dashboard module: per-role aggregates + live 'ops' event forwarding to screens."""

from fastapi import FastAPI

from app.core import events
from app.core.realtime import hub
from app.core.roles import Role
from app.modules.dashboard.router import router

# Events that change what a dashboard shows. Clients treat these as "refresh" hints.
LIVE_EVENTS = [
    "TripsGenerated", "TripStarted", "StopArrived", "TripEnded", "TripCancelled",
    "StudentBoarded", "TripDelayed", "TripDelayResolved", "CapacityWarning", "OverCapacity",
    "UnallocatedBoarding", "AttendanceFinalized", "BusRunsReassigned",
]


async def _forward(ev: events.Event) -> None:
    data = {"event": ev.type, "payload": ev.payload, "occurred_at": ev.occurred_at}
    await hub.send_to_role(Role.ADMIN, "ops", data)
    await hub.send_to_role(Role.SECURITY, "ops", data)
    if route_id := ev.payload.get("route_id"):
        await hub.send_to_topic(f"route:{route_id}", "ops", data)
    if driver_id := ev.payload.get("driver_id"):
        await hub.send_to_user(driver_id, "ops", data)


def register(app: FastAPI) -> None:
    for t in LIVE_EVENTS:
        events.subscribe(t, _forward)


__all__ = ["router", "register"]
