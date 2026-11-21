from __future__ import annotations

import csv
import io
import json
import time
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .domain_engine import SYSTEM_PROMPT, compute_project_result
from .knowledge_base import KnowledgeBase
from .llm_client import LLMCallError, LLMClient
from .schemas import (
    AssistantMessageOut,
    ChatMessage,
    CreateSessionResponse,
    MessageResponse,
    ProjectResult,
    SendMessageRequest,
    SessionStateResponse,
)
from .storage import Storage, utc_now_iso

WELCOME_TEXT = (
    "Я помогу понять, где в вашей инфраструктуре поставить «Синоникс» и межсетевой экран, "
    "а также посчитаю минимальное количество правил передачи данных и файлов. "
    "Опишите две сети и что между ними нужно передавать."
)

EXAMPLE_PROMPT = (
    "Есть закрытая сеть цеха и офисная сеть. Два сервера цеха отправляют журналы на сервер в офисе по UDP 514. "
    "Сервер в офисе опрашивает контроллер по Modbus TCP. Инженер из офиса передаёт в цех файлы программ "
    "для станков, их нужно проверять антивирусом."
)

app = FastAPI(title="Synonyx 1.9 Architecture Assistant API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

storage = Storage(settings.db_path)
kb = KnowledgeBase(settings.kb_dir)
llm = LLMClient(settings, storage)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/sessions", response_model=CreateSessionResponse, status_code=201)
def create_session() -> CreateSessionResponse:
    session_id = f"sess_{uuid.uuid4().hex[:12]}"
    storage.create_session(session_id)
    telemetry = storage.get_session_telemetry(session_id)
    return CreateSessionResponse(
        session_id=session_id,
        status="needs_clarification",
        welcome_message=WELCOME_TEXT,
        example_prompt=EXAMPLE_PROMPT,
        telemetry=telemetry,
    )


@app.get("/api/sessions/{session_id}", response_model=SessionStateResponse)
def get_session(session_id: str) -> SessionStateResponse:
    row = storage.get_session_row(session_id)
    if not row:
        raise HTTPException(status_code=404, detail="Сессия не найдена")

    messages = storage.get_messages(session_id)
    result = (
        ProjectResult.model_validate_json(row["result_json"])
        if row["result_json"]
        else None
    )
    telemetry = storage.get_session_telemetry(session_id)
    return SessionStateResponse(
        session_id=session_id,
        status=row["status"],
        welcome_message=WELCOME_TEXT,
        example_prompt=EXAMPLE_PROMPT,
        messages=messages,
        result=result,
        telemetry=telemetry,
    )


@app.post("/api/sessions/{session_id}/messages", response_model=MessageResponse)
async def send_message(session_id: str, req: SendMessageRequest) -> Any:
    row = storage.get_session_row(session_id)
    if not row:
        raise HTTPException(status_code=404, detail="Сессия не найдена")

    cached = storage.get_idempotent_response(session_id, req.client_request_id)
    if cached is not None:
        return MessageResponse.model_validate(cached)

    t0 = time.monotonic()
    started_at = utc_now_iso()
    next_turn = int(row["turn_counter"]) + 1

    prev_result = (
        ProjectResult.model_validate_json(row["result_json"])
        if row["result_json"]
        else None
    )
    draft_state: dict[str, Any] = json.loads(row["draft_state_json"] or "{}")

    user_parts: list[str] = []
    if req.text.strip():
        user_parts.append(req.text.strip())
    vendor_new: list[tuple[str, str, str]] = []
    for ans in req.answers:
        if ans.is_unknown:
            user_parts.append(f"[{ans.question_id}]: Не знаю")
        elif ans.other_text:
            user_parts.append(f"[{ans.question_id}]: Другое — {ans.other_text}")
            vendor_new.append(("other_option", ans.other_text, ans.other_text.strip()))
        elif ans.selected_options:
            user_parts.append(f"[{ans.question_id}]: {', '.join(ans.selected_options)}")

    user_text = "\n".join(user_parts).strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Пустое сообщение")

    kb_context, kb_sources = kb.search(user_text)
    history = storage.get_messages(session_id)

    system_sections = [
        SYSTEM_PROMPT,
        f"Фрагменты базы знаний (synonyx_base):\n{kb_context}",
    ]
    if prev_result:
        system_sections.append(
            f"Текущая конфигурация проекта: {prev_result.model_dump_json(by_alias=True, exclude={'diagram_drawio_xml'})}"
        )

    llm_messages: list[dict[str, str]] = [
        {"role": "system", "content": "\n\n".join(system_sections)}
    ]
    for h in history[-8:]:
        llm_messages.append({"role": h.role, "content": h.text})
    llm_messages.append({"role": "user", "content": user_text})

    try:
        llm_data = await llm.chat_json(
            session_id=session_id,
            turn_id=next_turn,
            purpose="dialog_and_extraction",
            messages=llm_messages,
        )
    except LLMCallError as exc:
        duration_ms = int((time.monotonic() - t0) * 1000)
        storage.record_step_timing(
            session_id, next_turn, started_at, utc_now_iso(), duration_ms, "error"
        )
        return JSONResponse(
            status_code=502,
            content={
                "error": {
                    "code": "LLM_CALL_FAILED",
                    "message": str(exc),
                    "retryable": exc.retryable,
                    "client_request_id": req.client_request_id,
                }
            },
        )

    for req_txt in llm_data.get("unsupported_requests") or []:
        if req_txt:
            vendor_new.append(("unsupported_request", user_text, str(req_txt).strip()))

    storage.add_vendor_requests(session_id, next_turn, vendor_new)
    all_vendor = [
        v["normalized_request"] for v in storage.get_vendor_requests(session_id)
    ]

    status, new_result, questions = compute_project_result(
        llm_data=llm_data,
        prev_result=prev_result,
        kb_sources=kb_sources,
        answers=req.answers,
        vendor_requests_history=all_vendor,
    )

    assistant_text = str(llm_data.get("assistant_text") or "Конфигурация обновлена.")
    storage.append_message(
        session_id,
        next_turn,
        ChatMessage(
            id=f"msg_{uuid.uuid4().hex[:10]}",
            role="user",
            text=user_text,
            timestamp=started_at,
        ),
    )
    storage.append_message(
        session_id,
        next_turn,
        ChatMessage(
            id=f"msg_{uuid.uuid4().hex[:10]}",
            role="assistant",
            text=assistant_text,
            sources=kb_sources,
            clarification_questions=questions,
            timestamp=utc_now_iso(),
        ),
    )

    draft_state["last_intent"] = llm_data.get("intent")
    storage.update_session_state(session_id, status, next_turn, draft_state, new_result)

    duration_ms = int((time.monotonic() - t0) * 1000)
    storage.record_step_timing(
        session_id, next_turn, started_at, utc_now_iso(), duration_ms, "ok"
    )

    telemetry = storage.get_session_telemetry(session_id, turn_timing_ms=duration_ms)
    resp_obj = MessageResponse(
        session_id=session_id,
        turn_id=next_turn,
        status=status,
        assistant_message=AssistantMessageOut(
            text=assistant_text,
            sources=kb_sources,
            clarification_questions=questions,
        ),
        result=new_result,
        telemetry=telemetry,
    )
    storage.save_idempotent_response(
        session_id, req.client_request_id, resp_obj.model_dump(by_alias=True)
    )
    return resp_obj


@app.get("/api/sessions/{session_id}/export/drawio")
def export_drawio(session_id: str) -> Response:
    row = storage.get_session_row(session_id)
    if not row or not row["result_json"]:
        raise HTTPException(status_code=404, detail="Схема ещё не построена")

    result = ProjectResult.model_validate_json(row["result_json"])
    if not result.diagram_drawio_xml:
        raise HTTPException(status_code=404, detail="XML схемы отсутствует")

    return Response(
        content=result.diagram_drawio_xml,
        media_type="application/xml; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="synonyx_{session_id}.drawio"'
        },
    )


@app.get("/api/sessions/{session_id}/export/json")
def export_json(session_id: str) -> dict[str, Any]:
    row = storage.get_session_row(session_id)
    if not row or not row["result_json"]:
        raise HTTPException(status_code=404, detail="Результат ещё не сформирован")

    result = ProjectResult.model_validate_json(row["result_json"])
    telemetry = storage.get_session_telemetry(session_id)

    data = result.model_dump(by_alias=True, exclude={"diagram_drawio_xml"})
    data["schema_version"] = settings.schema_version
    data["session_id"] = session_id
    data["status"] = row["status"]
    data["usage"] = telemetry.model_dump()
    return data


@app.get("/api/sessions/{session_id}/export/logs")
def export_session_logs(
    session_id: str,
    format: str = Query("jsonl", pattern="^(json|jsonl|csv)$"),
) -> Response:
    logs = storage.get_logs(session_id)
    return _format_logs_response(logs, format, f"synonyx_logs_{session_id}.{format}")


@app.get("/api/export/logs")
def export_all_logs(
    format: str = Query("jsonl", pattern="^(json|jsonl|csv)$"),
) -> Response:
    logs = storage.get_logs(None)
    return _format_logs_response(logs, format, f"synonyx_all_logs.{format}")


def _format_logs_response(
    logs: list[dict[str, Any]], fmt: str, filename: str
) -> Response:
    if fmt == "json":
        body = json.dumps(logs, ensure_ascii=False, indent=2)
        media = "application/json; charset=utf-8"
    elif fmt == "jsonl":
        body = "\n".join(json.dumps(r, ensure_ascii=False) for r in logs)
        media = "application/x-ndjson; charset=utf-8"
    else:
        buf = io.StringIO()
        if logs:
            writer = csv.DictWriter(buf, fieldnames=list(logs[0].keys()))
            writer.writeheader()
            writer.writerows(logs)
        body = buf.getvalue()
        media = "text/csv; charset=utf-8"

    return Response(
        content=body,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/sessions/{session_id}/export/vendor-requests")
def export_session_vendor_requests(session_id: str) -> list[dict[str, Any]]:
    return storage.get_vendor_requests(session_id)


@app.get("/api/export/vendor-requests")
def export_all_vendor_requests() -> list[dict[str, Any]]:
    return storage.get_vendor_requests(None)


@app.get("/api/meta/models")
def get_models_meta() -> dict[str, Any]:
    return {
        "models": [
            {
                "model_id": settings.llm_model_id,
                "provider": settings.llm_provider,
                "purpose": "Диалог, извлечение параметров и классификация намерений",
                "openrouter_url": settings.llm_openrouter_url,
                "p_input_usd_per_1m": settings.llm_p_input_usd_per_1m,
                "p_output_usd_per_1m": settings.llm_p_output_usd_per_1m,
            }
        ],
        "knowledge_base_indexing_cost": {
            "total_cost_usd": 0.0,
            "total_tokens": 0,
            "note": "Индексация synonyx_base выполняется локально по ключевым словам без вызова платных эмбеддингов",
        },
    }
