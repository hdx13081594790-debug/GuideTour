from datetime import datetime
from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin


class Device(Base, TimestampMixin):
    __tablename__ = "device"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_session_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    device_type: Mapped[str] = mapped_column(String(32), default="glass")
    language: Mapped[str] = mapped_column(String(16), default="zh")
    status: Mapped[str] = mapped_column(String(32), default="online")
    battery_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_heading: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_pitch: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_roll: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
