from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.realtime.connection_manager import connection_manager

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await connection_manager.connect(session_id, websocket)
    try:
        while True:
            message = await websocket.receive_text()
            if message == "ping":
                await connection_manager.send(websocket, {"type": "pong", "session_id": session_id})
    except WebSocketDisconnect:
        connection_manager.disconnect(session_id, websocket)
