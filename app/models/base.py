from datetime import UTC, datetime
from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# SQLAlchemy 模型基类。
#
# 所有 app/models/*.py 的表模型都继承 Base；
# init_db() 和 Alembic 都依赖 Base.metadata 收集表结构。


class Base(DeclarativeBase):
    # DeclarativeBase 让 SQLAlchemy 能通过类定义映射数据库表。
    pass


class TimestampMixin:
    # 通用时间字段。业务表继承这个 mixin 后自动拥有 created_at/updated_at。
    # 这些字段用于追踪 POI、设备、导航任务、照片等记录的生命周期。
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
