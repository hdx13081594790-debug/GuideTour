from collections import defaultdict
from typing import Any

from fastapi import WebSocket
from fastapi.encoders import jsonable_encoder
from starlette.websockets import WebSocketState

# WebSocket 连接管理器。
#
# 这个类不关心“导航/位置/视觉”的具体业务，只维护：
# session_id -> 多个 WebSocket 连接
#
# 数据流：
# 1. 前端打开 /api/v1/ws/s001；
# 2. connect() 把连接记录到 _connections["s001"]；
# 3. 业务路由调用 broadcast("s001", event)；
# 4. 同一会话的手机端/眼镜端同时收到 JSON 事件。


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[session_id].add(websocket)
        await self.send(websocket, {"type": "connected", "session_id": session_id})

    def disconnect(self, session_id: str, websocket: WebSocket) -> None:
        connections = self._connections.get(session_id)
        if not connections:
            return
        connections.discard(websocket)
        if not connections:
            self._connections.pop(session_id, None)

    async def send(self, websocket: WebSocket, event: dict[str, Any]) -> None:
        # jsonable_encoder 可以把 Pydantic 模型、datetime 等转换成
        # WebSocket 可序列化的 JSON 数据。
        if websocket.application_state == WebSocketState.CONNECTED:
            await websocket.send_json(jsonable_encoder(event))

    async def broadcast(self, session_id: str, event: dict[str, Any]) -> None:
        # 广播时如果发现连接已经失效，收集后统一清理，避免连接池越来越脏。
        connections = list(self._connections.get(session_id, set()))
        stale: list[WebSocket] = []
        for websocket in connections:
            try:
                await self.send(websocket, event)
            except RuntimeError:
                stale.append(websocket)
        for websocket in stale:
            self.disconnect(session_id, websocket)


connection_manager = ConnectionManager()
