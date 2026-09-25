from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, Integer, SmallInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models import Base, TimestampMixin, str_enum

if TYPE_CHECKING:
    from app.modules.auth.models import User


class BusStatus(str, Enum):
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    RETIRED = "retired"


class Bus(Base, TimestampMixin):
    __tablename__ = "buses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    registration_no: Mapped[str] = mapped_column(String(20), unique=True)
    capacity: Mapped[int] = mapped_column(SmallInteger)
    model: Mapped[str | None] = mapped_column(String(80))
    status: Mapped[BusStatus] = mapped_column(
        str_enum(BusStatus, "bus_status"), default=BusStatus.ACTIVE
    )
    # The bus's regular driver. A driver is assigned to at most one bus (unique).
    driver_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), unique=True)

    # Read-only link to auth's User for display (master_data never writes users).
    driver: Mapped["User | None"] = relationship("User", lazy="selectin", viewonly=True)

    @property
    def driver_name(self) -> str | None:
        return self.driver.full_name if self.driver else None


class Stop(Base, TimestampMixin):
    __tablename__ = "stops"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    landmark: Mapped[str | None] = mapped_column(String(160))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)


class Route(Base, TimestampMixin):
    __tablename__ = "routes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(10), unique=True)  # shown on the route badge, e.g. "14"
    name: Mapped[str] = mapped_column(String(120))
    color: Mapped[str] = mapped_column(String(7))  # "#RRGGBB" line colour
    description: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    stops: Mapped[list["RouteStop"]] = relationship(
        back_populates="route",
        order_by="RouteStop.sequence",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class RouteStop(Base):
    """A stop's position on a route.

    Convention: sequence 1 is the first pickup point, the LAST stop is the campus.
    `offset_min` = minutes after the trip's departure from stop 1 (pickup direction).
    Drop trips run the list in reverse (see trips module).
    """

    __tablename__ = "route_stops"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("routes.id", ondelete="CASCADE"), index=True)
    stop_id: Mapped[int] = mapped_column(ForeignKey("stops.id", ondelete="RESTRICT"))
    sequence: Mapped[int] = mapped_column(SmallInteger)
    offset_min: Mapped[int] = mapped_column(SmallInteger)

    route: Mapped[Route] = relationship(back_populates="stops")
    stop: Mapped[Stop] = relationship(lazy="selectin")

    __table_args__ = (
        # Deferred so a reorder can swap sequences inside one transaction.
        UniqueConstraint("route_id", "sequence", name="uq_route_stops_route_seq",
                         deferrable=True, initially="DEFERRED"),
        UniqueConstraint("route_id", "stop_id", name="uq_route_stops_route_stop"),
    )
