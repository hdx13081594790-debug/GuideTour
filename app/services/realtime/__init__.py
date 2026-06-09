
"""实时通信服务包。

目前主要封装 WebSocket 连接管理。
导航、位置、视觉等业务模块通过 connection_manager 向同一 session 广播事件。
"""
