from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin


class PhotoAsset(Base, TimestampMixin):
    __tablename__ = "photo_asset"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    device_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    related_poi_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
