from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any, Optional

from .schemas import (
    ChatMessage,
    ModelBreakdownItem,
    ProjectResult,
    SessionStatus,
    TelemetryInfo,
    UsageStatus,
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Storage:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    turn_counter INTEGER NOT NULL DEFAULT 0,
                    draft_state_json TEXT NOT NULL DEFAULT '{}',
                    result_json TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    turn_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    text TEXT NOT NULL,
                    sources_json TEXT NOT NULL DEFAULT '[]',
                    questions_json TEXT NOT NULL DEFAULT '[]',
                    timestamp TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS idempotency (
                    session_id TEXT NOT NULL,
                    client_request_id TEXT NOT NULL,
                    response_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (session_id, client_request_id)
                );

                CREATE TABLE IF NOT EXISTS llm_calls (
                    call_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    turn_id INTEGER NOT NULL,
                    provider_response_id TEXT,
                    model_id TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    purpose TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    finished_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    prompt_tokens INTEGER,
                    completion_tokens INTEGER,
                    cached_tokens INTEGER,
                    reasoning_tokens INTEGER,
                    p_input REAL NOT NULL,
                    p_output REAL NOT NULL,
                    estimated_cost_input REAL,
                    estimated_cost_output REAL,
                    estimated_cost_total REAL,
                    provider_usage_cost REAL,
                    usage_source TEXT NOT NULL,
                    raw_usage_json TEXT
                );

                CREATE TABLE IF NOT EXISTS step_timings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    turn_id INTEGER NOT NULL,
                    started_at TEXT NOT NULL,
                    finished_at TEXT NOT NULL,
                    duration_ms INTEGER NOT NULL,
                    status TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS vendor_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    turn_id INTEGER NOT NULL,
                    source TEXT NOT NULL,
                    raw_text TEXT NOT NULL,
                    normalized_request TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    def create_session(self, session_id: str) -> None:
        now = utc_now_iso()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO sessions (session_id, status, turn_counter, draft_state_json, result_json, created_at, updated_at)
                VALUES (?, 'needs_clarification', 0, '{}', NULL, ?, ?)
                """,
                (session_id, now, now),
            )

    def get_session_row(self, session_id: str) -> Optional[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
            ).fetchone()

    def get_idempotent_response(
        self, session_id: str, client_request_id: str
    ) -> Optional[dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT response_json FROM idempotency WHERE session_id = ? AND client_request_id = ?",
                (session_id, client_request_id),
            ).fetchone()
            if row:
                return json.loads(row["response_json"])
            return None

    def save_idempotent_response(
        self, session_id: str, client_request_id: str, response_dict: dict[str, Any]
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO idempotency (session_id, client_request_id, response_json, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, client_request_id, json.dumps(response_dict, ensure_ascii=False), utc_now_iso()),
            )

    def append_message(self, session_id: str, turn_id: int, msg: ChatMessage) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO messages (id, session_id, turn_id, role, text, sources_json, questions_json, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    msg.id,
                    session_id,
                    turn_id,
                    msg.role,
                    msg.text,
                    json.dumps([s.model_dump() for s in msg.sources], ensure_ascii=False),
                    json.dumps(
                        [q.model_dump() for q in msg.clarification_questions],
                        ensure_ascii=False,
                    ),
                    msg.timestamp,
                ),
            )

    def get_messages(self, session_id: str) -> list[ChatMessage]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM messages WHERE session_id = ? ORDER BY rowid ASC",
                (session_id,),
            ).fetchall()
        out: list[ChatMessage] = []
        for r in rows:
            out.append(
                ChatMessage(
                    id=r["id"],
                    role=r["role"],
                    text=r["text"],
                    sources=json.loads(r["sources_json"]),
                    clarification_questions=json.loads(r["questions_json"]),
                    timestamp=r["timestamp"],
                )
            )
        return out

    def update_session_state(
        self,
        session_id: str,
        status: SessionStatus,
        turn_counter: int,
        draft_state: dict[str, Any],
        result: Optional[ProjectResult],
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE sessions
                SET status = ?, turn_counter = ?, draft_state_json = ?, result_json = ?, updated_at = ?
                WHERE session_id = ?
                """,
                (
                    status,
                    turn_counter,
                    json.dumps(draft_state, ensure_ascii=False),
                    result.model_dump_json(by_alias=True) if result else None,
                    utc_now_iso(),
                    session_id,
                ),
            )

    def record_llm_call(self, record: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO llm_calls (
                    call_id, session_id, turn_id, provider_response_id, model_id, provider,
                    purpose, started_at, finished_at, status, prompt_tokens, completion_tokens,
                    cached_tokens, reasoning_tokens, p_input, p_output,
                    estimated_cost_input, estimated_cost_output, estimated_cost_total,
                    provider_usage_cost, usage_source, raw_usage_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["call_id"],
                    record["session_id"],
                    record["turn_id"],
                    record.get("provider_response_id"),
                    record["model_id"],
                    record["provider"],
                    record["purpose"],
                    record["started_at"],
                    record["finished_at"],
                    record["status"],
                    record.get("prompt_tokens"),
                    record.get("completion_tokens"),
                    record.get("cached_tokens"),
                    record.get("reasoning_tokens"),
                    record["p_input"],
                    record["p_output"],
                    record.get("estimated_cost_input"),
                    record.get("estimated_cost_output"),
                    record.get("estimated_cost_total"),
                    record.get("provider_usage_cost"),
                    record["usage_source"],
                    json.dumps(record.get("raw_usage"), ensure_ascii=False)
                    if record.get("raw_usage") is not None
                    else None,
                ),
            )

    def record_step_timing(
        self,
        session_id: str,
        turn_id: int,
        started_at: str,
        finished_at: str,
        duration_ms: int,
        status: str,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO step_timings (session_id, turn_id, started_at, finished_at, duration_ms, status)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (session_id, turn_id, started_at, finished_at, duration_ms, status),
            )

    def add_vendor_requests(
        self,
        session_id: str,
        turn_id: int,
        items: list[tuple[str, str, str]],
    ) -> None:
        if not items:
            return
        now = utc_now_iso()
        with self._connect() as conn:
            for source, raw_text, normalized in items:
                exists = conn.execute(
                    "SELECT 1 FROM vendor_requests WHERE session_id = ? AND normalized_request = ?",
                    (session_id, normalized),
                ).fetchone()
                if not exists:
                    conn.execute(
                        """
                        INSERT INTO vendor_requests (session_id, turn_id, source, raw_text, normalized_request, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (session_id, turn_id, source, raw_text, normalized, now),
                    )

    def get_vendor_requests(self, session_id: Optional[str] = None) -> list[dict[str, Any]]:
        with self._connect() as conn:
            if session_id:
                rows = conn.execute(
                    "SELECT session_id, turn_id, source, raw_text, normalized_request, created_at FROM vendor_requests WHERE session_id = ? ORDER BY id ASC",
                    (session_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT session_id, turn_id, source, raw_text, normalized_request, created_at FROM vendor_requests ORDER BY id ASC"
                ).fetchall()
        return [dict(r) for r in rows]

    def get_session_telemetry(
        self, session_id: str, turn_timing_ms: Optional[int] = None
    ) -> TelemetryInfo:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM llm_calls WHERE session_id = ? ORDER BY started_at ASC",
                (session_id,),
            ).fetchall()

        if not rows:
            return TelemetryInfo(
                turn_timing_ms=turn_timing_ms,
                usage_status="confirmed",
                total_cost_usd=0.0,
                total_input_tokens=0,
                total_output_tokens=0,
                models_breakdown=[],
            )

        unknown_count = 0
        total_in = 0
        total_out = 0
        total_cost = 0.0
        provider_cost_sum = 0.0
        has_provider_cost = False
        by_model: dict[tuple[str, str], dict[str, Any]] = {}

        for r in rows:
            key = (r["model_id"], r["provider"])
            if key not in by_model:
                by_model[key] = {
                    "model_id": r["model_id"],
                    "provider": r["provider"],
                    "calls_count": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cost_input_usd": 0.0,
                    "cost_output_usd": 0.0,
                    "cost_total_usd": 0.0,
                    "has_unknown": False,
                }
            entry = by_model[key]
            entry["calls_count"] += 1

            if r["usage_source"] == "unknown" or r["prompt_tokens"] is None:
                unknown_count += 1
                entry["has_unknown"] = True
            else:
                p_tok = int(r["prompt_tokens"])
                c_tok = int(r["completion_tokens"] or 0)
                c_in = float(r["estimated_cost_input"] or 0.0)
                c_out = float(r["estimated_cost_output"] or 0.0)
                c_tot = float(r["estimated_cost_total"] or 0.0)

                total_in += p_tok
                total_out += c_tok
                total_cost += c_tot

                entry["input_tokens"] += p_tok
                entry["output_tokens"] += c_tok
                entry["cost_input_usd"] += c_in
                entry["cost_output_usd"] += c_out
                entry["cost_total_usd"] += c_tot

            if r["provider_usage_cost"] is not None:
                has_provider_cost = True
                provider_cost_sum += float(r["provider_usage_cost"])

        usage_status: UsageStatus = "confirmed"
        if unknown_count == len(rows):
            usage_status = "unknown"
        elif unknown_count > 0:
            usage_status = "partial"

        breakdown = [
            ModelBreakdownItem(
                model_id=v["model_id"],
                provider=v["provider"],
                calls_count=v["calls_count"],
                input_tokens=v["input_tokens"],
                output_tokens=v["output_tokens"],
                cost_input_usd=None if v["has_unknown"] else round(v["cost_input_usd"], 10),
                cost_output_usd=None if v["has_unknown"] else round(v["cost_output_usd"], 10),
                cost_total_usd=None if v["has_unknown"] else round(v["cost_total_usd"], 10),
            )
            for v in by_model.values()
        ]

        return TelemetryInfo(
            turn_timing_ms=turn_timing_ms,
            usage_status=usage_status,
            total_cost_usd=None if usage_status == "unknown" else round(total_cost, 10),
            provider_actual_cost_usd=round(provider_cost_sum, 10) if has_provider_cost else None,
            total_input_tokens=total_in,
            total_output_tokens=total_out,
            models_breakdown=breakdown,
        )

    def get_logs(self, session_id: Optional[str] = None) -> list[dict[str, Any]]:
        with self._connect() as conn:
            if session_id:
                calls = conn.execute(
                    "SELECT * FROM llm_calls WHERE session_id = ? ORDER BY started_at ASC",
                    (session_id,),
                ).fetchall()
                timings = conn.execute(
                    "SELECT * FROM step_timings WHERE session_id = ? ORDER BY id ASC",
                    (session_id,),
                ).fetchall()
            else:
                calls = conn.execute(
                    "SELECT * FROM llm_calls ORDER BY started_at ASC"
                ).fetchall()
                timings = conn.execute(
                    "SELECT * FROM step_timings ORDER BY id ASC"
                ).fetchall()

        timing_map = {(t["session_id"], t["turn_id"]): t["duration_ms"] for t in timings}
        out: list[dict[str, Any]] = []
        for c in calls:
            d = dict(c)
            d["turn_timing_ms"] = timing_map.get((c["session_id"], c["turn_id"]))
            out.append(d)
        return out
