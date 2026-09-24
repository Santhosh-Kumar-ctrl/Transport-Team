"""Delay monitor module: turns late starts, late stop check-ins, overdue stops and
manual reports into TripDelayed / TripDelayResolved events."""

from fastapi import FastAPI

from app.core import events, tasks
from app.core.config import settings
from app.core.db import SessionLocal
from app.modules.delay_monitor import service
from app.modules.delay_monitor.models import DelaySource
from app.modules.delay_monitor.router import router
from app.modules.trips import service as trips_service


async def _on_started(ev: events.Event) -> None:
    async with SessionLocal() as session:
        trip = await trips_service.get_trip(session, ev.payload["trip_id"])
        await service.evaluate(session, trip, ev.payload["delay_min"], DelaySource.START, at_sequence=1)
        await session.commit()


async def _on_arrived(ev: events.Event) -> None:
    async with SessionLocal() as session:
        trip = await trips_service.get_trip(session, ev.payload["trip_id"])
        await service.evaluate(session, trip, ev.payload["delay_min"], DelaySource.STOP_ARRIVAL,
                               at_sequence=ev.payload["sequence"])
        await session.commit()


async def _watch() -> None:
    async with SessionLocal() as session:
        await service.watch_once(session)
        await session.commit()


def register(app: FastAPI) -> None:
    events.subscribe("TripStarted", _on_started)
    events.subscribe("StopArrived", _on_arrived)
    tasks.every(settings.delay_watch_interval_seconds, "delay-watcher", _watch)


__all__ = ["router", "register"]
