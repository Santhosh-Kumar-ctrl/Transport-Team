"""Boarding module: rotating trip QR, student check-in, roster, attendance."""

from fastapi import FastAPI

from app.core import events
from app.core.db import SessionLocal
from app.core.realtime import hub
from app.modules.boarding import service
from app.modules.boarding.router import router


async def _push_boarding(ev: events.Event) -> None:
    """Live update for the driver's boarded list / seat count."""
    data = {k: ev.payload[k] for k in
            ("trip_id", "student_id", "student_name", "allocation_match", "method", "boarded_count")}
    await hub.send_to_user(ev.payload["driver_id"], "boarding", data)
    await hub.send_to_topic(f"trip:{ev.payload['trip_id']}", "boarding", data)


async def _finalize(ev: events.Event) -> None:
    async with SessionLocal() as session:
        await service.finalize_attendance(session, ev.payload["trip_id"])
        await session.commit()


def register(app: FastAPI) -> None:
    events.subscribe("StudentBoarded", _push_boarding)
    events.subscribe("TripEnded", _finalize)


__all__ = ["router", "register"]
