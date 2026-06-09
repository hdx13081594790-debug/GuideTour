from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.realtime.connection_manager import connection_manager

# WebSocket 入口。
#
# 前端连接 /api/v1/ws/{session_id} 后，会被放入对应 session 的连接池。
# 导航、位置、视觉等路由在状态变化时调用 connection_manager.broadcast，
# 所有同 session 的客户端就能实时收到事件，不需要轮询 HTTP。

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    # 这里只保留一个很轻的 ping/pong，用于前端判断连接是否活着。
    # 业务事件由其他路由主动 broadcast。
    await connection_manager.connect(session_id, websocket)
    try:
        while True:
            message = await websocket.receive_text()
            if message == "ping":
                await connection_manager.send(websocket, {"type": "pong", "session_id": session_id})
    except WebSocketDisconnect:
        connection_manager.disconnect(session_id, websocket)
