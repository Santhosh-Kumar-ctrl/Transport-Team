from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.modules.boarding.models import AttendanceStatus
from app.modules.trips.models import Direction, TripStatus


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    type: str
    aggregate_type: str | None
    aggregate_id: int | None
    actor_id: int | None
    actor_name: str | None = None
    payload: dict
    occurred_at: datetime


class TripReport(BaseModel):
    trip_id: int
    service_date: date
    route_id: int
    route_code: str
    route_color: str
    direction: Direction
    bus_registration_no: str
    driver_name: str
    status: TripStatus
    scheduled_departure: datetime
    started_at: datetime | None
    ended_at: datetime | None
    max_delay_min: int
    delay_alerts: int
    boarded: int
    present: int
    absent: int


class AttendanceRow(BaseModel):
    service_date: date
    trip_id: int
    route_code: str
    direction: Direction
    student_id: int
    student_name: str
    roll_no: str | None
    status: AttendanceStatus
    boarded_at: datetime | None
