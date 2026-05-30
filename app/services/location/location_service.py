import json

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import get_settings
from app.schemas.location import LocationState, LocationUpdateRequest


class InMemoryLocationStore:
    def __init__(self) -> None:
        self._data: dict[str, LocationState] = {}

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


location_store = RedisLocationStore(get_settings().redis_url)
