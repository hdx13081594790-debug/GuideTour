from sqlalchemy.orm import Session
from app.models.interaction_log import InteractionLog

# SessionRepository 当前只负责写交互日志。
#
# 数据流：
# GuideAgent.chat() 处理完用户输入
# -> SessionRepository.log()
# -> interaction_log 表保存输入、意图、工具调用和回答。
# 后续可扩展会话上下文、用户画像、对话历史等能力。


class SessionRepository:
    def __init__(self, db: Session):
        self.db = db

    def log(self, session_id: str, device_id: str | None, input_type: str, user_text: str | None, intent: str | None, tool_called: str | None, response_text: str | None, related_poi_id: int | None = None) -> None:
        # 日志写入不影响前端响应结构，但对调试 Agent 决策很重要。
        self.db.add(InteractionLog(
            user_session_id=session_id,
            device_id=device_id,
            input_type=input_type,
            user_text=user_text,
            intent=intent,
            tool_called=tool_called,
            response_text=response_text,
            related_poi_id=related_poi_id,
        ))
        self.db.commit()
