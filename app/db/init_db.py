from app.models.base import Base
import app.models  # noqa: F401
from app.core.config import get_settings
from app.db.session import engine

# 数据库初始化入口。
#
# main.py 的 lifespan 启动阶段会调用 init_db()。
# MVP 为了开箱可跑，允许 auto_create_tables=True 时自动创建表；
# 正式项目更推荐使用 Alembic 迁移控制表结构演进。


def init_db() -> None:
    # AUTO_CREATE_TABLES=false 时不自动建表，交给 Alembic 或外部部署脚本。
    if not get_settings().auto_create_tables:
        return
    Base.metadata.create_all(bind=engine)
