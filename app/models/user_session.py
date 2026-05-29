from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin


class UserSession(Base, TimestampMixin):
    __tablename__ = "user_session"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    language: Mapped[str] = mapped_column(String(16), default="zh")
    current_poi_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
