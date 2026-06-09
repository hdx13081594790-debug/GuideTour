from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from app.core.config import get_settings

# SQLAlchemy 会话工厂。
#
# 数据流：
# 路由层 Depends(get_db) -> 生成一个 Session
# -> Repository/Service 使用这个 Session 读写数据库
# -> 请求结束后 finally 关闭 Session。
#
# 注意：Redis 状态不走这里；Redis Store 在 services/*/state_store.py 中管理。


settings = get_settings()
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def get_db() -> Generator[Session, None, None]:
    # FastAPI 依赖函数：每个 HTTP 请求独立一个数据库会话。
    # yield 后的 finally 确保请求完成或异常时都能释放连接。
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
