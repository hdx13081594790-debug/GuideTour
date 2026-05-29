from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str = "ok"


class ActionResult(BaseModel):
    type: str
    status: str = "triggered"
    message: str | None = None
    task_id: str | None = None
