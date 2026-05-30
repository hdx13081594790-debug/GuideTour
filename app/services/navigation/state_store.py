import json
import time

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import get_settings
from app.schemas.navigation import NavigationState


class InMemoryNavigationStateStore:
    def __init__(self) -> None:
        self.by_task: dict[str, NavigationState] = {}
        self.active_by_session: dict[str, str] = {}

    def save(self, state: NavigationState) -> NavigationState:
        self.by_task[state.task_id] = state
        if state.status == "navigating":
            self.active_by_session[state.session_id] = state.task_id
        elif self.active_by_session.get(state.session_id) == state.task_id:
            self.active_by_session.pop(state.session_id, None)
        return state

    def get(self, task_id: str) -> NavigationState | None:
        return self.by_task.get(task_id)

    def active_for_session(self, session_id: str) -> NavigationState | None:
        task_id = self.active_by_session.get(session_id)
        return self.get(task_id) if task_id else None


class RedisNavigationStateStore:
    def __init__(self, redis_url: str, fallback: InMemoryNavigationStateStore | None = None, ttl_seconds: int = 24 * 3600) -> None:
        self.redis = Redis.from_url(redis_url, decode_responses=True)
        self.fallback = fallback or InMemoryNavigationStateStore()
        self.ttl_seconds = ttl_seconds

    @staticmethod
    def task_key(task_id: str) -> str:
        return f"guide:navigation:{task_id}:state"

    @staticmethod
    def active_session_key(session_id: str) -> str:
        return f"guide:session:{session_id}:active_navigation"

    def save(self, state: NavigationState) -> NavigationState:
        state.updated_at = time.time()
        self.fallback.save(state)
        try:
            self.redis.set(self.task_key(state.task_id), state.model_dump_json(), ex=self.ttl_seconds)
            session_key = self.active_session_key(state.session_id)
            if state.status == "navigating":
                self.redis.set(session_key, state.task_id, ex=self.ttl_seconds)
            else:
                self.redis.delete(session_key)
        except RedisError:
            pass
        return state

    def get(self, task_id: str) -> NavigationState | None:
        try:
            raw = self.redis.get(self.task_key(task_id))
            if raw:
                return NavigationState.model_validate(json.loads(raw))
        except (RedisError, json.JSONDecodeError, ValueError):
            pass
        return self.fallback.get(task_id)

    def active_for_session(self, session_id: str) -> NavigationState | None:
        try:
            task_id = self.redis.get(self.active_session_key(session_id))
            if task_id:
                return self.get(task_id)
        except RedisError:
            pass
        return self.fallback.active_for_session(session_id)


navigation_state_store = RedisNavigationStateStore(get_settings().redis_url)
