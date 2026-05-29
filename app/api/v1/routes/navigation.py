from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.repositories.navigation_repo import NavigationRepository
from app.schemas.navigation import NavigationUpdateRequest, NavigationUpdateResponse, NearestRequest, RouteRequest, RouteResponse, StopNavigationRequest
from app.services.navigation.navigation_service import NavigationService

router = APIRouter(prefix="/navigation", tags=["navigation"])


@router.post("/route", response_model=RouteResponse)
async def route(payload: RouteRequest, db: Session = Depends(get_db)):
    return await NavigationService(db).plan_route(payload)


@router.post("/nearest", response_model=RouteResponse)
async def nearest(payload: NearestRequest, db: Session = Depends(get_db)):
    return await NavigationService(db).nearest_route(payload.session_id, payload.origin, payload.target_type, payload.radius_meters)


@router.post("/update-position", response_model=NavigationUpdateResponse)
def update_position(payload: NavigationUpdateRequest, db: Session = Depends(get_db)):
    return NavigationService(db).update_position(payload.task_id, payload.location)


@router.post("/stop")
def stop(payload: StopNavigationRequest, db: Session = Depends(get_db)):
    return {"task_id": NavigationService(db).stop(payload.session_id, payload.task_id), "status": "cancelled"}


@router.get("/{task_id}", response_model=RouteResponse)
def get_task(task_id: str, db: Session = Depends(get_db)):
    from app.core.exceptions import AppError
    repo = NavigationRepository(db)
    task = repo.get(task_id)
    if not task:
        raise AppError("导航任务不存在", 404)
    return repo.to_response(task)
