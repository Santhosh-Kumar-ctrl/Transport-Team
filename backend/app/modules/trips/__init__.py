"""Trips module: schedules, daily trip generation, start/arrive/end workflow."""

from fastapi import FastAPI

from app.core import events, tasks
from app.core.config import settings
from app.core.db import SessionLocal
from app.modules.trips.router import router
from app.modules.trips.service import generate_trips, reassign_bus_driver


async def _generate_today() -> None:
    async with SessionLocal() as session:
        await generate_trips(session)
        await session.commit()


async def _on_bus_driver_assigned(ev: events.Event) -> None:
    """The bus's new regular driver takes over its schedules and upcoming trips."""
    if ev.payload["driver_id"] is None:
        return  # driver removed: existing runs keep their driver until someone is assigned
    async with SessionLocal() as session:
        await reassign_bus_driver(session, ev.payload["bus_id"], ev.payload["driver_id"], actor_id=ev.actor_id)
        await session.commit()


def register(app: FastAPI) -> None:
    # Ensures today's trips exist at startup and keeps checking (covers midnight rollover).
    tasks.every(settings.trip_generation_interval_seconds, "trip-generator", _generate_today)
    events.subscribe("BusDriverAssigned", _on_bus_driver_assigned)


__all__ = ["router", "register"]
