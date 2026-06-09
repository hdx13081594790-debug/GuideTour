from pydantic import BaseModel

# 通用响应模型。
#
# schemas 目录只定义“数据形状”，不做业务逻辑。
# 路由层用这些模型声明 response_model，让 FastAPI 自动校验和生成 OpenAPI。


class HealthResponse(BaseModel):
    # /health 的固定返回，用于确认后端进程可访问。
    status: str = "ok"


class ActionResult(BaseModel):
    # Agent/视觉/手势接口的通用动作描述。
    # 前端根据 type/status/task_id 等字段决定是否更新 UI。
    type: str
    status: str = "triggered"
    message: str | None = None
    task_id: str | None = None
