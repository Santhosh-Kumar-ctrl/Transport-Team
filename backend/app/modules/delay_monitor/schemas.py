from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.delay_monitor.models import DelaySource


class ReportDelayIn(BaseModel):
    delay_min: int = Field(ge=1, le=300)
    reason: str = Field(min_length=3, max_length=255)


class DelayReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    trip_id: int
    source: DelaySource
    delay_min: int
    at_sequence: int | None
    reason: str | None
    reported_by: int | None
    created_at: datetime


class AffectedStop(BaseModel):
    sequence: int
    stop_id: int
    stop_name: str
    scheduled_at: datetime
    expected_at: datetime
