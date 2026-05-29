from sqlalchemy.orm import Session
from app.schemas.navigation import DestinationRef, RouteRequest
from app.schemas.photo import PhotoCaptureRequest
from app.services.navigation.navigation_service import NavigationService
from app.services.photo.photo_service import PhotoService
from app.services.rag.mock_rag_client import MockRAGClient


async def plan_route_tool(db: Session, session_id: str, origin: dict, destination_name: str | None = None, destination_poi_id: int | None = None):
    return await NavigationService(db).plan_route(RouteRequest(session_id=session_id, origin=origin, destination=DestinationRef(poi_id=destination_poi_id, name=destination_name)))


async def explain_poi_tool(poi_id: int, question: str | None = None, style: str = "normal"):
    return await MockRAGClient().answer(question or "介绍一下这个景点", poi_id=poi_id, context={"style": style})


def take_photo_tool(db: Session, session_id: str, frame_id: str | None = None):
    return PhotoService(db).capture(PhotoCaptureRequest(session_id=session_id, frame_id=frame_id))
