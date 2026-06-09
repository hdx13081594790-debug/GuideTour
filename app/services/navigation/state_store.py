import json
import time

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import get_settings
from app.schemas.navigation import NavigationState

# 导航状态存储层。
#
# 为什么不只存数据库？
# navigation_task 适合保存任务历史，但导航中每 1-3 秒更新一次位置，
# 如果每次都完全依赖数据库，会让实时状态恢复和 WebSocket 推送变慢。
#
# 这里采用 Redis + 内存兜底：
# - Redis：跨进程、可恢复、适合当前导航状态；
# - InMemory：Redis 断开时仍可在当前进程内继续演示。


class InMemoryNavigationStateStore:
    # 仅用于兜底和测试。生产多进程部署时，不同进程的内存不共享，
    # 所以真实运行主要依赖 RedisNavigationStateStore。
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
        # 写 Redis 前先写内存兜底。即使 Redis 暂时失败，
        # 当前进程仍可读取最近一次状态。
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
        # 前端刷新后可通过 session_id 找回当前活动导航任务，
        # 不需要知道 task_id。
        try:
            task_id = self.redis.get(self.active_session_key(session_id))
            if task_id:
                return self.get(task_id)
        except RedisError:
            pass
        return self.fallback.active_for_session(session_id)


# 全局单例：服务层直接 import 使用。
# MVP 简化了依赖注入；后续如果做测试隔离/多租户，可以改成 FastAPI Depends。
navigation_state_store = RedisNavigationStateStore(get_settings().redis_url)
