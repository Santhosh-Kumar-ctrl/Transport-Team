from datetime import date, datetime

from pydantic import BaseModel

from app.modules.allocation.schemas import MyAllocation
from app.modules.capacity.schemas import Level, RouteUtilization
from app.modules.history.schemas import EventOut
from app.modules.trips.models import Direction, TripStatus
from app.modules.trips.schemas import RouteBrief, TripDetail


class NextStop(BaseModel):
    sequence: int
    name: str
    scheduled_at: datetime
    expected_at: datetime


class BoardRow(BaseModel):
    """One line of the admin departure board."""

    trip_id: int
    route: RouteBrief
    direction: Direction
    bus_registration_no: str
    driver_name: str
    status: TripStatus
    scheduled_departure: datetime
    started_at: datetime | None
    delay_min: int
    next_stop: NextStop | None
    stops_total: int
    stops_done: int
    boarded: int
    capacity: int
    occupancy_level: Level
    allocated: int


class TripCounts(BaseModel):
    scheduled: int = 0
    in_progress: int = 0
    completed: int = 0
    cancelled: int = 0
    delayed_now: int = 0


class AdminDashboard(BaseModel):
    service_date: date
    counts: TripCounts
    board: list[BoardRow]
    alerts: list[EventOut]
    utilization: list[RouteUtilization]


class DriverTrip(BaseModel):
    trip: TripDetail
    delay_min: int
    boarded: int
    capacity: int
    occupancy_level: Level


class DriverDashboard(BaseModel):
    service_date: date
    active: DriverTrip | None
    trips: list[DriverTrip]


class MyStopView(BaseModel):
    stop_id: int
    name: str
    sequence: int
    scheduled_at: datetime
    expected_at: datetime
    arrived_at: datetime | None


class StudentTrip(BaseModel):
    trip_id: int
    direction: Direction
    status: TripStatus
    scheduled_departure: datetime
    started_at: datetime | None
    bus_registration_no: str
    delay_min: int
    my_stop: MyStopView | None
    next_stop_name: str | None
    stops_done: int
    stops_total: int
    boarded: bool
    boarded_at: datetime | None


class StudentDashboard(BaseModel):
    service_date: date
    allocation: MyAllocation | None
    trips: list[StudentTrip]
    unread_notifications: int
