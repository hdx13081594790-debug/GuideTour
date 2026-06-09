from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin

# 景点建筑扩展表。
#
# POI 表只保存“点位”；scenic_building 保存建筑/景点的文化讲解元数据，
# 例如朝向、推荐观看距离、RAG collection 名称等。
# MVP 中主要预留结构，后续真实 RAG 和视觉识别会用它增强讲解。


class ScenicBuilding(Base, TimestampMixin):
    __tablename__ = "scenic_building"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    poi_id: Mapped[int] = mapped_column(ForeignKey("poi.id"), index=True)
    name: Mapped[str] = mapped_column(String(128), index=True)
    dynasty: Mapped[str | None] = mapped_column(String(64), nullable=True)
    historical_tags: Mapped[str | None] = mapped_column(Text, default="")
    story_keywords: Mapped[str | None] = mapped_column(Text, default="")
    bounding_polygon: Mapped[str | None] = mapped_column(Text, nullable=True)
    front_direction_degree: Mapped[float | None] = mapped_column(Float, nullable=True)
    recommended_view_distance_min: Mapped[float] = mapped_column(Float, default=10)
    recommended_view_distance_max: Mapped[float] = mapped_column(Float, default=120)
    default_intro: Mapped[str | None] = mapped_column(Text, default="")
    rag_collection_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
