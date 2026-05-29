from sqlalchemy.orm import Session
from app.models.interaction_log import InteractionLog


class SessionRepository:
    def __init__(self, db: Session):
        self.db = db

    def log(self, session_id: str, device_id: str | None, input_type: str, user_text: str | None, intent: str | None, tool_called: str | None, response_text: str | None, related_poi_id: int | None = None) -> None:
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
