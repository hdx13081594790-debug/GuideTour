from app.models.base import Base
from app.models.poi import POI
from app.models.scenic_building import ScenicBuilding
from app.models.user_session import UserSession
from app.models.device import Device
from app.models.navigation_task import NavigationTask
from app.models.interaction_log import InteractionLog
from app.models.photo_asset import PhotoAsset

# 这里集中 import 所有模型，目的是让 SQLAlchemy/Alembic 能通过
# app.models 一次性加载全部表定义。
#
# 数据流：
# init_db.py / alembic/env.py import app.models
# -> 各模型类被注册到 Base.metadata
# -> create_all 或 Alembic autogenerate 才能看到完整 schema。

__all__ = [
    "Base",
    "POI",
    "ScenicBuilding",
    "UserSession",
    "Device",
    "NavigationTask",
    "InteractionLog",
    "PhotoAsset",
]
