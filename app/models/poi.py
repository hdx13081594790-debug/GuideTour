from sqlalchemy import Boolean, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin

# POI 表：园区内所有可搜索、可导航、可讲解的位置点。
#
# 数据流：
# scripts/seed_poi.py 写入基础 POI；
# POIRepository 负责查询；
# NavigationService 用 POI 坐标规划路线；
# FovService 用 POI 坐标和 priority 判断视野候选。


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
