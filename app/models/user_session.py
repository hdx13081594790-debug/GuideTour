from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin

# 用户会话表。
#
# session_id 是前端、WebSocket、导航任务、交互日志之间的关联主线。
# MVP 里 session_id 多由前端固定传入；生产环境可以由登录/设备绑定流程创建。


class UserSession(Base, TimestampMixin):
    __tablename__ = "user_session"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    language: Mapped[str] = mapped_column(String(16), default="zh")
    current_poi_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
