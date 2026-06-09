from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import get_settings
import app.models  # noqa: F401
from app.models.base import Base

# Alembic 迁移环境配置。
#
# Alembic 的职责是管理数据库结构版本：
# - upgrade：把数据库升级到新 schema；
# - downgrade：回滚 schema。
#
# 它和 init_db() 的区别：
# - init_db() 是 MVP 启动时自动 create_all，适合本地演示；
# - Alembic 是正式项目的结构变更记录，适合团队协作和生产部署。
#
# 数据流：
# alembic 命令 -> env.py -> 读取 Settings.database_url
# -> 加载 app.models 到 Base.metadata
# -> 执行 versions/*.py 中的 upgrade/downgrade。

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    # 迁移使用和应用相同的 DATABASE_URL，避免“应用连一个库、迁移改另一个库”。
    return get_settings().database_url


def run_migrations_offline() -> None:
    # offline 模式不建立真实数据库连接，只生成 SQL 文本。
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    # online 模式连接数据库并真正执行迁移。
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(configuration, prefix="sqlalchemy.", poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
