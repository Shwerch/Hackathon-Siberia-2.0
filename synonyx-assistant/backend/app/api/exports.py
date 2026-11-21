from fastapi import APIRouter, HTTPException, Response
from app.api import sessions as sess_api

router = APIRouter(prefix="/api/sessions/{session_id}/export", tags=["exports"])


@router.get("/drawio")
def download_drawio(session_id: str) -> Response:
    state = sess_api.storage.load_session(session_id)
    if not state or not state.drawio_xml:
        raise HTTPException(status_code=404, detail="Схема ещё не построена")
    return Response(
        content=state.drawio_xml,
        media_type="application/xml",
        headers={"Content-Disposition": f'attachment; filename="synonyx_{session_id[:8]}.drawio"'},
    )


@router.get("/result.json")
def export_result_json(session_id: str) -> dict:
    state = sess_api.storage.load_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    return {
        "schema_version": state.schema_version,
        "session_id": state.session_id,
        "status": state.status,
        "networks": [n.model_dump() for n in state.networks],
        "firewall": {"side": state.firewall_side},
        "synonyx": {"location": "closed", "node_a_faces": "open", "node_b_faces": "closed"},
        "rules": [r.model_dump(by_alias=True) for r in state.rules],
        "rules_count": state.rules_count,
        "file_users_count": state.file_users_count,
        "file_users_range": state.file_users_range,
        "unknowns": state.unknowns,
        "assumptions": state.assumptions,
        "devices": [d.model_dump() for d in state.devices],
        "sources": [s.model_dump() for s in state.sources],
        "requests_for_vendor": state.requests_for_vendor,
        "usage": state.usage.model_dump(),
        "timing": state.timing.model_dump(),
    }


@router.get("/logs")
def export_logs(session_id: str, format: str = "jsonl") -> Response:
    if format == "csv":
        data = sess_api.storage.export_logs_csv(session_id)
        return Response(content=data, media_type="text/csv")
    data = sess_api.storage.export_logs_jsonl(session_id)
    return Response(content=data, media_type="application/x-ndjson")
