"""Capacity module: live occupancy + route utilisation + capacity alerts."""

from fastapi import FastAPI

from app.core import events
from app.core.db import SessionLocal
from app.modules.capacity import service
from app.modules.capacity.router import router


async def _on_boarded(ev: events.Event) -> None:
    async with SessionLocal() as session:
        await service.check_trip_capacity(session, ev.payload["trip_id"])
        await session.commit()


def register(app: FastAPI) -> None:
    events.subscribe("StudentBoarded", _on_boarded)


__all__ = ["router", "register"]
