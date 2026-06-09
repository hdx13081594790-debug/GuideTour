import json

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import get_settings
from app.schemas.location import LocationState, LocationUpdateRequest

# 位置状态存储层。
#
# 前端/眼镜端会周期性 POST /location/update，把 lng/lat/heading/pitch 等
# 写入这里。后续 Agent、自动讲解、导航纠偏都可以读取最近位置。
#
# 与导航状态类似，这里也采用 Redis + 内存兜底：
# - Redis key guide:session:{session_id}:context 保存会话当前位置；
# - Redis key guide:device:{device_id}:location 保存设备当前位置；
# - Redis 不可用时退回 InMemoryLocationStore，方便本地演示。


class InMemoryLocationStore:
    def __init__(self) -> None:
        self._data: dict[str, LocationState] = {}

    def update(self, payload: LocationUpdateRequest) -> LocationState:
        # 写入顺序：先写内存兜底，再尝试写 Redis。
        # 这样 Redis 断开时，请求仍能成功返回当前进程内的位置。
        state = LocationState(
            session_id=payload.session_id,
            device_id=payload.device_id,
            location=payload.location,
            heading=payload.heading,
            pitch=payload.pitch,
            roll=payload.roll,
            accuracy_meters=payload.accuracy_meters,
        )
        self._data[payload.session_id] = state
        return state

    def get(self, session_id: str) -> LocationState | None:
        return self._data.get(session_id)


class RedisLocationStore:
    def __init__(self, redis_url: str, fallback: InMemoryLocationStore | None = None, ttl_seconds: int = 3600) -> None:
        self.redis = Redis.from_url(redis_url, decode_responses=True)
        self.fallback = fallback or InMemoryLocationStore()
        self.ttl_seconds = ttl_seconds

    @staticmethod
    def session_key(session_id: str) -> str:
        return f"guide:session:{session_id}:context"

    @staticmethod
    def device_key(device_id: str) -> str:
        return f"guide:device:{device_id}:location"

    def update(self, payload: LocationUpdateRequest) -> LocationState:
        state = LocationState(
            session_id=payload.session_id,
            device_id=payload.device_id,
            location=payload.location,
            heading=payload.heading,
            pitch=payload.pitch,
            roll=payload.roll,
            accuracy_meters=payload.accuracy_meters,
        )
        self.fallback.update(payload)
        try:
            value = state.model_dump_json()
            self.redis.set(self.session_key(payload.session_id), value, ex=self.ttl_seconds)
            self.redis.set(self.device_key(payload.device_id), value, ex=self.ttl_seconds)
        except RedisError:
            pass
        return state

    def get(self, session_id: str) -> LocationState | None:
        try:
            raw = self.redis.get(self.session_key(session_id))
            if raw:
                return LocationState.model_validate(json.loads(raw))
        except (RedisError, json.JSONDecodeError, ValueError):
            pass
        return self.fallback.get(session_id)

# 全局位置状态仓库。路由层直接 import 使用。
location_store = RedisLocationStore(get_settings().redis_url)
