from sqlalchemy import Boolean, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin


class POI(Base, TimestampMixin):
    __tablename__ = "poi"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), index=True)
    alias_names: Mapped[str | None] = mapped_column(Text, default="")
    poi_type: Mapped[str] = mapped_column(String(32), index=True)
    description: Mapped[str | None] = mapped_column(Text, default="")
    longitude: Mapped[float] = mapped_column(Float)
    latitude: Mapped[float] = mapped_column(Float)
    altitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    map_provider: Mapped[str | None] = mapped_column(String(32), default="local")
    amap_poi_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    baidu_uid: Mapped[str | None] = mapped_column(String(128), nullable=True)
    area_name: Mapped[str | None] = mapped_column(String(128), default="颐和园")
    is_accessible: Mapped[bool] = mapped_column(Boolean, default=True)
    opening_status: Mapped[str] = mapped_column(String(32), default="open")
    priority: Mapped[int] = mapped_column(Integer, default=5)
