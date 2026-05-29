from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin


class InteractionLog(Base, TimestampMixin):
    __tablename__ = "interaction_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_session_id: Mapped[str] = mapped_column(String(64), index=True)
    device_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    input_type: Mapped[str] = mapped_column(String(32), default="text")
    user_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    intent: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tool_called: Mapped[str | None] = mapped_column(String(128), nullable=True)
    response_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    related_poi_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
