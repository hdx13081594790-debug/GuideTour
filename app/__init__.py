
"""颐和园 AI 导览后端应用包。

目录分层：
- api：FastAPI 路由层，负责 HTTP/WebSocket 入口；
- schemas：Pydantic 请求/响应模型；
- models：SQLAlchemy 数据库表模型；
- repositories：数据库访问封装；
- services：业务服务、地图/RAG/Agent/视觉等能力；
- core/db：配置、日志、异常、数据库基础设施。
"""
