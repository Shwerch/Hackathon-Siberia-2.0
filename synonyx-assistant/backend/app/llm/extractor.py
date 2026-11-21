import json
from typing import Any
from app.llm.client import TrackedLLMClient
from app.llm.prompts import EXTRACTOR_SYSTEM_PROMPT
from app.models.state import SessionState
from app.models.usage import CallLogEntry


async def extract_intent_and_delta(
    llm: TrackedLLMClient,
    state: SessionState,
    user_message: str,
    turn_id: int,
) -> tuple[dict[str, Any], CallLogEntry]:
    compact_state = {
        "status": state.status,
        "networks": [n.model_dump() for n in state.networks],
        "devices": [d.model_dump() for d in state.devices],
        "flows": [f.model_dump() for f in state.flows],
        "pending_questions": [q.model_dump() for q in state.pending_questions],
    }
    history_tail = [{"role": m.role, "content": m.content} for m in state.messages[-4:]]

    messages = [
        {"role": "system", "content": EXTRACTOR_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Текущее состояние:\n{json.dumps(compact_state, ensure_ascii=False)}\n\n"
                f"Последние сообщения:\n{json.dumps(history_tail, ensure_ascii=False)}\n\n"
                f"Новое сообщение пользователя:\n{user_message}"
            ),
        },
    ]
    raw, log_entry = await llm.chat_completion(
        session_id=state.session_id,
        turn_id=turn_id,
        purpose="extract_intent",
        messages=messages,
        temperature=0.0,
        max_tokens=1200,
        json_mode=True,
    )
    if log_entry.status != "ok":
        return {"intent": "error", "error": log_entry.error_message}, log_entry

    try:
        parsed = llm.parse_json_safe(raw)
    except Exception:
        parsed = {"intent": "unclear", "raw": raw}
    return parsed, log_entry
