import copy
import json
import time
import uuid
from fastapi import APIRouter, HTTPException
from app.engine.clarifier import build_clarifications
from app.engine.drawio_builder import build_drawio_xml
from app.engine.rule_calculator import recalculate_rules
from app.engine.validator import validate_and_normalize_state
from app.llm.client import TrackedLLMClient
from app.llm.extractor import extract_intent_and_delta
from app.llm.prompts import REPLY_SYSTEM_PROMPT
from app.models.state import (
    ChatMessage,
    FlowDraft,
    NetworkItem,
    SessionState,
    SourceRef,
    TurnRequest,
)
from app.models.usage import CallLogEntry, TurnTiming
from app.rag.retriever import KBRetriever
from app.storage.db import SessionStorage

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

storage: SessionStorage
llm_client: TrackedLLMClient
kb_retriever: KBRetriever


def _record_usage(state: SessionState, entry: CallLogEntry) -> None:
    if not storage.append_call_log(entry):
        return
    state.usage.calls.append(entry)
    if entry.usage_status == "confirmed":
        state.usage.input_tokens += entry.input_tokens or 0
        state.usage.output_tokens += entry.output_tokens or 0
        state.usage.input_cost_usd += entry.evaluation_input_cost_usd or 0.0
        state.usage.output_cost_usd += entry.evaluation_output_cost_usd or 0.0
        state.usage.evaluation_cost_usd += entry.evaluation_cost_usd or 0.0
        if entry.actual_cost_usd is not None:
            state.usage.actual_cost_usd = (state.usage.actual_cost_usd or 0.0) + entry.actual_cost_usd
    else:
        state.usage.status = "partial_unknown"


@router.post("", response_model=SessionState)
async def create_session() -> SessionState:
    sid = str(uuid.uuid4())
    state = SessionState(session_id=sid)
    storage.save_session(state)
    return state


@router.get("/{session_id}", response_model=SessionState)
async def get_session(session_id: str) -> SessionState:
    state = storage.load_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    return state


@router.post("/{session_id}/turn", response_model=SessionState)
async def process_turn(session_id: str, req: TurnRequest) -> SessionState:
    state = storage.load_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Сессия не найдена")

    t_start = time.perf_counter()
    state.turn_counter += 1
    turn_id = state.turn_counter

    user_text_parts = [req.message.strip()]
    for qid, ans in req.clarification_answers.items():
        if ans.get("other_text"):
            other_val = str(ans["other_text"]).strip()
            if other_val and other_val not in state.requests_for_vendor:
                state.requests_for_vendor.append(other_val)
            if qid not in state.dismissed_questions:
                state.dismissed_questions.append(qid)
            user_text_parts.append(f"{qid}: другое ({other_val})")
        elif ans.get("choice"):
            choice_val = str(ans["choice"]).strip()
            if choice_val.lower() == "не знаю" and qid not in state.dismissed_questions:
                state.dismissed_questions.append(qid)
            user_text_parts.append(f"{qid}: {choice_val}")

    combined_msg = "\n".join(p for p in user_text_parts if p)

    state.messages.append(ChatMessage(role="user", content=combined_msg, turn_id=turn_id))
    backup_state = copy.deepcopy(state)

    delta, extract_log = await extract_intent_and_delta(llm_client, state, combined_msg, turn_id)
    _record_usage(state, extract_log)

    intent = delta.get("intent", "project_update")
    if intent == "unclear" and delta.get("upsert_flows"):
        intent = "project_update"

    warnings: list[str] = []

    if intent == "project_update":
        if delta.get("networks"):
            state.networks = [NetworkItem(**n) for n in delta["networks"][:2]]
        if "both_initially_open" in delta:
            state.both_initially_open = bool(delta["both_initially_open"])
        if delta.get("firewall_side") in ("open", "both"):
            state.firewall_side = delta["firewall_side"]

        existing = {f.flow_key: f for f in state.flows}
        for f_data in delta.get("upsert_flows", []):
            fk = f_data["flow_key"]
            if fk in existing:
                merged = existing[fk].model_dump()
                for k, v in f_data.items():
                    if v is not None and v != [] and v != "":
                        merged[k] = v
                existing[fk] = FlowDraft(**merged)
            else:
                existing[fk] = FlowDraft(**f_data)

        for rk in delta.get("remove_flow_keys", []):
            existing.pop(rk, None)

        for ren in delta.get("rename_devices", []):
            for f in existing.values():
                f.source_devices = [ren["new_name"] if d == ren["old_name"] else d for d in f.source_devices]
                f.target_devices = [ren["new_name"] if d == ren["old_name"] else d for d in f.target_devices]
        for rem in delta.get("remove_devices", []):
            for f in list(existing.values()):
                if rem in f.target_devices or rem in f.source_devices:
                    f.target_devices = [d for d in f.target_devices if d != rem]
                    f.source_devices = [d for d in f.source_devices if d != rem]
                    if not f.target_devices or not f.source_devices:
                        existing.pop(f.flow_key, None)

        state.flows = list(existing.values())
        for req_v in delta.get("requests_for_vendor", []):
            if req_v not in state.requests_for_vendor:
                state.requests_for_vendor.append(req_v)

        warnings = validate_and_normalize_state(state)
        if state.status == "unsupported":
            state.rules = backup_state.rules
            state.rules_count = backup_state.rules_count
            state.drawio_xml = backup_state.drawio_xml
        else:
            recalculate_rules(state)
            new_questions, all_unknowns = build_clarifications(state)
            state.pending_questions = new_questions
            state.unknowns = all_unknowns
            if not state.flows and not state.networks:
                state.status = "needs_clarification"
            elif state.unknowns:
                state.status = "preliminary"
            else:
                state.status = "completed"
            state.drawio_xml = build_drawio_xml(state) if state.rules else ""

    elif intent in ("invalid_edit", "ambiguous_edit", "out_of_scope_networks"):
        warnings.append(delta.get("clarification_needed_reason") or "Запрос требует уточнения или выходит за рамки кейса.")

    kb_chunks = kb_retriever.search(combined_msg, top_k=3)
    sources = [SourceRef(file=c.file, section=c.section) for c in kb_chunks]
    state.sources = sources

    kb_context = "\n\n".join(f"[{c.file} | {c.section}]\n{c.text}" for c in kb_chunks)
    calc_context = json.dumps(
        {
            "intent": intent,
            "status": state.status,
            "rules_count": state.rules_count,
            "rules": [r.model_dump(by_alias=True) for r in state.rules],
            "file_users_count": state.file_users_count,
            "unknowns": state.unknowns,
            "requests_for_vendor": state.requests_for_vendor,
            "warnings": warnings,
            "pending_questions": [q.text for q in state.pending_questions],
        },
        ensure_ascii=False,
    )

    reply_text, reply_log = await llm_client.chat_completion(
        session_id=state.session_id,
        turn_id=turn_id,
        purpose="generate_reply",
        messages=[
            {"role": "system", "content": REPLY_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Вопрос/сообщение пользователя: {combined_msg}\n\n"
                    f"Результаты Rule Engine:\n{calc_context}\n\n"
                    f"Фрагменты БЗ:\n{kb_context}"
                ),
            },
        ],
        temperature=0.2,
        max_tokens=2000,
    )
    _record_usage(state, reply_log)

    if reply_log.status != "ok" or not reply_text.strip():
        reply_text = "Произошла ошибка при обращении к языковой модели. Повторите запрос — введённые данные сохранены."
        turn_status = "error"
    else:
        state.last_explanation = reply_text
        turn_status = "ok"

    state.messages.append(
        ChatMessage(
            role="assistant",
            content=reply_text,
            turn_id=turn_id,
            questions=state.pending_questions if intent != "question_about_scheme" else [],
            sources=sources,
        )
    )

    elapsed = round(time.perf_counter() - t_start, 3)
    state.timing.turns.append(TurnTiming(turn_id=turn_id, duration_seconds=elapsed, status=turn_status))  # type: ignore[arg-type]
    state.timing.mean_turn_seconds = round(
        sum(t.duration_seconds for t in state.timing.turns) / len(state.timing.turns), 3
    )

    storage.save_session(state)
    return state
