from collections import defaultdict
from typing import Any

from fastapi import WebSocket
from fastapi.encoders import jsonable_encoder
from starlette.websockets import WebSocketState


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
        if websocket.application_state == WebSocketState.CONNECTED:
            await websocket.send_json(jsonable_encoder(event))

    async def broadcast(self, session_id: str, event: dict[str, Any]) -> None:
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
