from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin


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
