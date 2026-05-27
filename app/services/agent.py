from __future__ import annotations

from app import repository
from app.services.language import detect_language
from app.services.qa import answer_question


def run_guide_agent(session_id: str, message: str, language: str | None, current_poi_id: str | None) -> dict:
    session = repository.get_session(session_id)
    final_language = language or session.get("language") or detect_language(message)
    final_poi_id = current_poi_id or session.get("current_poi_id")
    answer, citations, actions, intent = answer_question(message, final_language, final_poi_id)

    history = session.get("history", [])[-8:]
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": answer, "intent": intent})

    for action in actions:
        if action.get("type") == "set_current_poi":
            final_poi_id = action.get("poi_id")

    repository.update_session(session_id, final_language, final_poi_id, history)
    repository.log_qa(session_id, message, answer, intent)

    return {
        "session_id": session_id,
        "language": final_language,
        "answer": answer,
        "citations": citations,
        "suggested_actions": actions,
        "intent": intent,
    }
