from datetime import date, datetime
from enum import Enum

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base, str_enum


class BoardingMethod(str, Enum):
    QR = "qr"  # student scanned the driver's trip QR
    MANUAL = "manual"  # driver marked the student (no phone / camera issue)


class AttendanceStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    PRESENT_UNALLOCATED = "present_unallocated"  # rode a bus that isn't their allocated route


class Boarding(Base):
    __tablename__ = "boardings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    stop_id: Mapped[int | None] = mapped_column(ForeignKey("stops.id", ondelete="SET NULL"))
    method: Mapped[BoardingMethod] = mapped_column(str_enum(BoardingMethod, "boarding_method"))
    allocation_match: Mapped[bool] = mapped_column(Boolean)
    boarded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    recorded_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    __table_args__ = (UniqueConstraint("trip_id", "student_id", name="uq_boardings_trip_student"),)


class AttendanceRecord(Base):
    """Final per-trip attendance, written when the trip ends."""

    __tablename__ = "attendance_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("routes.id", ondelete="RESTRICT"))
    service_date: Mapped[date] = mapped_column(Date, index=True)
    status: Mapped[AttendanceStatus] = mapped_column(str_enum(AttendanceStatus, "attendance_status"))
    boarding_id: Mapped[int | None] = mapped_column(ForeignKey("boardings.id", ondelete="SET NULL"))

    __table_args__ = (UniqueConstraint("trip_id", "student_id", name="uq_attendance_trip_student"),)
