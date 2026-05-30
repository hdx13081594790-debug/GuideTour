from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.db.session import get_db
from app.repositories.navigation_repo import NavigationRepository
from app.schemas.navigation import NavigationState, NavigationUpdateRequest, NavigationUpdateResponse, NearestRequest, RouteRequest, RouteResponse, StopNavigationRequest
from app.services.navigation.navigation_service import NavigationService
from app.services.realtime.connection_manager import connection_manager

router = APIRouter(prefix="/navigation", tags=["navigation"])


@router.post("/route", response_model=RouteResponse)
async def route(payload: RouteRequest, db: Session = Depends(get_db)):
    service = NavigationService(db)
    response = await service.plan_route(payload)
    await _broadcast_navigation(payload.session_id, "navigation_started", response.task_id, service)
    return response


@router.post("/nearest", response_model=RouteResponse)
async def nearest(payload: NearestRequest, db: Session = Depends(get_db)):
    service = NavigationService(db)
    response = await service.nearest_route(payload.session_id, payload.origin, payload.target_type, payload.radius_meters)
    await _broadcast_navigation(payload.session_id, "navigation_started", response.task_id, service)
    return response


@router.post("/update-position", response_model=NavigationUpdateResponse)
async def update_position(payload: NavigationUpdateRequest, db: Session = Depends(get_db)):
    service = NavigationService(db)
    response = service.update_position(payload.task_id, payload.location)
    state = service.get_state(payload.task_id)
    await connection_manager.broadcast(
        payload.session_id,
        {
            "type": "navigation_updated",
            "session_id": payload.session_id,
            "task_id": payload.task_id,
            "update": response,
            "state": state,
        },
    )
    return response


@router.post("/stop")
async def stop(payload: StopNavigationRequest, db: Session = Depends(get_db)):
    service = NavigationService(db)
    task_id = service.stop(payload.session_id, payload.task_id)
    state = service.get_state(task_id)
    await connection_manager.broadcast(
        payload.session_id,
        {
            "type": "navigation_stopped",
            "session_id": payload.session_id,
            "task_id": task_id,
            "state": state,
        },
    )
    return {"task_id": task_id, "status": "cancelled"}


@router.get("/session/{session_id}/active-state", response_model=NavigationState)
def get_active_state(session_id: str, db: Session = Depends(get_db)):
    state = NavigationService(db).get_active_state(session_id)
    if not state:
        raise AppError("当前会话没有正在进行的导航", 404)
    return state


@router.get("/{task_id}/state", response_model=NavigationState)
def get_task_state(task_id: str, db: Session = Depends(get_db)):
    state = NavigationService(db).get_state(task_id)
    if not state:
        raise AppError("导航状态不存在", 404)
    return state


@router.get("/{task_id}", response_model=RouteResponse)
def get_task(task_id: str, db: Session = Depends(get_db)):
    repo = NavigationRepository(db)
    task = repo.get(task_id)
    if not task:
        raise AppError("导航任务不存在", 404)
    return repo.to_response(task)


async def _broadcast_navigation(session_id: str, event_type: str, task_id: str, service: NavigationService) -> None:
    await connection_manager.broadcast(
        session_id,
        {
            "type": event_type,
            "session_id": session_id,
            "task_id": task_id,
            "state": service.get_state(task_id),
        },
    )
