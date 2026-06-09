from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin

# 交互日志表。
#
# GuideAgent 每处理一次用户输入都会写一条记录，包括原始文本、识别意图、
# 调用的工具、最终回答和关联 POI。
# 这是后续排查“为什么误导航/为什么回答不对”的重要依据。


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
