from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.db.session import get_db
from app.repositories.device_repo import DeviceRepository
from app.schemas.location import LocationState, LocationUpdateRequest
from app.services.location.location_service import location_store
from app.services.realtime.connection_manager import connection_manager

# 位置路由。
#
# 眼镜/手机端周期性调用 /location/update 上传位置和朝向。
# 数据会同时进入：
# - device 表：可持久查询设备最近状态；
# - RedisLocationStore：供实时导航/讲解读取；
# - WebSocket：推送给当前 session 的前端。

router = APIRouter(prefix="/location", tags=["location"])


@router.post("/update", response_model=LocationState)
async def update_location(payload: LocationUpdateRequest, db: Session = Depends(get_db)):
    # 持久状态和实时状态都更新，前端无需等待下一次轮询即可收到广播。
    DeviceRepository(db).update_location(payload)
    state = location_store.update(payload)
    await connection_manager.broadcast(
        payload.session_id,
        {
            "type": "location_updated",
            "session_id": payload.session_id,
            "device_id": payload.device_id,
            "location": state,
        },
    )
    return state


@router.get("/current/{session_id}", response_model=LocationState)
def current_location(session_id: str):
    # 用 session_id 读取最近位置。自动讲解、调试页面都可复用这个接口。
    state = location_store.get(session_id)
    if not state:
        raise AppError("当前会话还没有位置", 404)
    return state
