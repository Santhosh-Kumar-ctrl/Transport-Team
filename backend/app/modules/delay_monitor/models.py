from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base, str_enum


class DelaySource(str, Enum):
    START = "start"  # trip started late
    STOP_ARRIVAL = "stop_arrival"  # driver checked in at a stop late
    OVERDUE = "overdue"  # watcher: next stop's scheduled time passed with no check-in
    NOT_STARTED = "not_started"  # watcher: departure time passed, trip not started
    MANUAL = "manual"  # driver/admin reported it
    RECOVERED = "recovered"  # back under the threshold (resolution record)
    # Team B will add: GPS = "gps", ETA_MODEL = "eta_model"


class DelayReport(Base):
    """Every delay alert raised (and every recovery), one row each. The latest row per trip
    is the trip's current alert state."""

    __tablename__ = "delay_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), index=True)
    source: Mapped[DelaySource] = mapped_column(str_enum(DelaySource, "delay_source"))
    delay_min: Mapped[int] = mapped_column(SmallInteger)
    at_sequence: Mapped[int | None] = mapped_column(SmallInteger)
    reason: Mapped[str | None] = mapped_column(String(255))
    reported_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __mapper_args__ = {"eager_defaults": True}
