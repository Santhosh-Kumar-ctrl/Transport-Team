from enum import Enum

from pydantic import BaseModel


class Level(str, Enum):
    OK = "ok"
    WARNING = "warning"  # >= CAPACITY_WARN_PCT
    FULL = "full"  # exactly at capacity
    OVER = "over"  # more riders/allocations than seats
    UNKNOWN = "unknown"  # no capacity known (route without schedule)


class TripOccupancy(BaseModel):
    trip_id: int
    route_id: int
    bus_id: int
    boarded: int
    capacity: int
    pct: int
    level: Level


class RouteUtilization(BaseModel):
    route_id: int
    code: str
    name: str
    color: str
    allocated: int
    seat_capacity: int | None
    pct: int | None
    level: Level
    active_schedules: int
