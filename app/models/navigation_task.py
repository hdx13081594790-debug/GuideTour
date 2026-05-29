from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin


class NavigationTask(Base, TimestampMixin):
    __tablename__ = "navigation_task"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_session_id: Mapped[str] = mapped_column(String(64), index=True)
    origin_latitude: Mapped[float] = mapped_column(Float)
    origin_longitude: Mapped[float] = mapped_column(Float)
    destination_poi_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    destination_name: Mapped[str] = mapped_column(String(128))
    provider: Mapped[str] = mapped_column(String(32), default="local")
    status: Mapped[str] = mapped_column(String(32), default="planning")
    route_distance_meters: Mapped[float] = mapped_column(Float, default=0)
    route_duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    route_polyline: Mapped[str] = mapped_column(Text, default="[]")
    route_steps: Mapped[str] = mapped_column(Text, default="[]")
    current_step_index: Mapped[int] = mapped_column(Integer, default=0)
