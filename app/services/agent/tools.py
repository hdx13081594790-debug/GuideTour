from sqlalchemy.orm import Session
from app.schemas.navigation import DestinationRef, RouteRequest
from app.schemas.photo import PhotoCaptureRequest
from app.services.navigation.navigation_service import NavigationService
from app.services.photo.photo_service import PhotoService

# Agent 工具函数占位。
#
# 这些函数是给未来 LangGraph/LangChain 工具注册准备的薄封装。
# 当前 GuideAgent 直接调用 NavigationService/PhotoService/RAGClient，
# 但保留 tools.py 能让后续迁移到真正 graph workflow 时复用工具接口。


async def plan_route_tool(db: Session, session_id: str, origin: dict, destination_name: str | None = None, destination_poi_id: int | None = None):
    # 路线规划工具：把模型抽取的目的地槽位转换成 RouteRequest。
    return await NavigationService(db).plan_route(RouteRequest(session_id=session_id, origin=origin, destination=DestinationRef(poi_id=destination_poi_id, name=destination_name)))


def take_photo_tool(db: Session, session_id: str, frame_id: str | None = None):
    # 拍照工具：创建照片资产记录。
    return PhotoService(db).capture(PhotoCaptureRequest(session_id=session_id, frame_id=frame_id))
