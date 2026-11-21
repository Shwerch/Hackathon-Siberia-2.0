import csv
import io
import json
import sqlite3
from pathlib import Path
from typing import Optional
from app.models.state import SessionState
from app.models.usage import CallLogEntry


class SessionStorage:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS sessions (session_id TEXT PRIMARY KEY, state_json TEXT NOT NULL)"
            )
            conn.execute(
                """CREATE TABLE IF NOT EXISTS call_logs (
                    call_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    turn_id INTEGER NOT NULL,
                    payload_json TEXT NOT NULL
                )"""
            )

    def save_session(self, state: SessionState) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO sessions (session_id, state_json) VALUES (?, ?)",
                (state.session_id, state.model_dump_json(by_alias=True)),
            )

    def load_session(self, session_id: str) -> Optional[SessionState]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT state_json FROM sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
            if not row:
                return None
            return SessionState.model_validate_json(row[0])

    def append_call_log(self, entry: CallLogEntry) -> bool:
        """Сохраняет лог с дедупликацией по call_id. Возвращает True, если запись новая."""
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT OR IGNORE INTO call_logs (call_id, session_id, turn_id, payload_json) VALUES (?, ?, ?, ?)",
                (entry.call_id, entry.session_id, entry.turn_id, entry.model_dump_json()),
            )
            return cur.rowcount > 0

    def export_logs_jsonl(self, session_id: Optional[str] = None) -> str:
        with self._conn() as conn:
            if session_id:
                rows = conn.execute(
                    "SELECT payload_json FROM call_logs WHERE session_id = ? ORDER BY turn_id",
                    (session_id,),
                ).fetchall()
            else:
                rows = conn.execute("SELECT payload_json FROM call_logs ORDER BY session_id, turn_id").fetchall()
        return "\n".join(r[0] for r in rows)

    def export_logs_csv(self, session_id: Optional[str] = None) -> str:
        lines = self.export_logs_jsonl(session_id).splitlines()
        if not lines:
            return ""
        records = [json.loads(line) for line in lines]
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)
        return buf.getvalue()
