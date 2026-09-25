from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

from app.modules.boarding.models import AttendanceStatus, BoardingMethod
from app.modules.trips.models import Direction


class TripQR(BaseModel):
    token: str
    trip_id: int
    issued_at: datetime
    expires_at: datetime
    ttl_seconds: int
    route_code: str
    route_color: str
    bus_registration_no: str


class CheckInIn(BaseModel):
    token: str = Field(min_length=10)


class ManualBoardIn(BaseModel):
    student_id: int | None = None
    roll_no: str | None = None

    @model_validator(mode="after")
    def one_identifier(self) -> "ManualBoardIn":
        if (self.student_id is None) == (self.roll_no is None):
            raise ValueError("Provide exactly one of student_id or roll_no")
        return self


class BoardingReceipt(BaseModel):
    boarding_id: int
    trip_id: int
    student_id: int
    student_name: str
    boarded_at: datetime
    method: BoardingMethod
    allocation_match: bool
    route_code: str
    route_name: str
    route_color: str
    bus_registration_no: str
    stop_name: str | None
    boarded_count: int
    message: str


class RosterEntry(BaseModel):
    student_id: int
    full_name: str
    roll_no: str | None
    stop_id: int | None
    stop_name: str | None
    allocated: bool
    boarded: bool
    boarded_at: datetime | None
    method: BoardingMethod | None


class Roster(BaseModel):
    trip_id: int
    capacity: int
    allocated_count: int
    boarded_count: int
    entries: list[RosterEntry]


class AttendanceOut(BaseModel):
    trip_id: int
    service_date: date
    route_id: int
    route_code: str
    route_color: str
    direction: Direction
    status: AttendanceStatus
    boarded_at: datetime | None
