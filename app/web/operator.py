"""Operator-facing read-only UX data and safe local preferences."""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

router = APIRouter()


class Preferences(BaseModel):
    compact: bool = False
    advanced: bool = False
    monitor: bool = False


class Preview(BaseModel):
    message: str = Field(min_length=1, max_length=4000)




def build_notifications(radios: list[dict], last_poll_result: str, queue_depth: int) -> list[dict]:
    """Prioritized, read-only operator warnings (no external delivery)."""
    alerts = []
    enabled = [r for r in radios if r.get("enabled")]
    if not enabled:
        alerts.append({"level": "critical", "message": "No radios enabled for broadcasting."})
    elif not any(r.get("connected") for r in enabled):
        alerts.append({"level": "critical", "message": "All enabled radios are disconnected."})
    elif any(not r.get("connected") for r in enabled):
        alerts.append({"level": "warning", "message": "One or more enabled radios are disconnected."})
    if str(last_poll_result).lower().startswith("error"):
        alerts.append({"level": "warning", "message": "Weather polling reported an error."})
    if queue_depth > 5:
        alerts.append({"level": "warning", "message": "Transmit queue has more than five pending messages."})
    return alerts


@router.get("/api/ux/notifications")
async def notifications(request: Request):
    tx = request.app.state.tx
    poller = request.app.state.poller
    return {"notifications": build_notifications(tx.status(), poller.status.last_poll_result, tx.queue_depth)}


@router.get("/api/ux/overview")
async def overview(request: Request):
    db = request.app.state.db
    tx = request.app.state.tx
    poller = request.app.state.poller
    radios = tx.status()
    enabled = [r for r in radios if r["enabled"]]
    connected = [r for r in enabled if r["connected"]]
    health = ("critical" if not connected else "degraded" if len(connected) < len(enabled) else "healthy")
    try:
        history = [dict(row) for row in db.query_history(limit=15)]
    except Exception:
        history = []
    try:
        broadcasts = [dict(row) for row in db.query_transmit_log(limit=15)]
    except Exception:
        broadcasts = []
    return {
        "health": health,
        "notifications": build_notifications(radios, poller.status.last_poll_result, tx.queue_depth),
        "radios": radios,
        "queue_depth": tx.queue_depth,
        "uptime_seconds": poller.status.uptime_seconds,
        "last_poll": poller.status.last_poll_time,
        "last_poll_result": poller.status.last_poll_result,
        "last_error": tx.last_error,
        "weather_history": history,
        "broadcast_history": broadcasts,
        "connection_history": tx.connection_history(),
        "dry_run": db.get_setting("dry_run", True),
    }


@router.post("/api/ux/preview")
async def preview(payload: Preview):
    from ..config import MAX_PAYLOAD_BYTES
    encoded = payload.message.encode("utf-8")
    clipped = payload.message
    while len(clipped.encode("utf-8")) > MAX_PAYLOAD_BYTES:
        clipped = clipped[:-1]
    return {
        "preview": clipped,
        "bytes": len(encoded),
        "limit": MAX_PAYLOAD_BYTES,
        "truncated": clipped != payload.message,
        "transmitted": False,
    }


@router.get("/api/ux/preferences")
async def preferences(request: Request):
    db = request.app.state.db
    return {k: str(db.get_setting("ux_" + k, "false")).lower() in ("true", "1", "yes")
            for k in ("compact", "advanced", "monitor")}


@router.post("/api/ux/preferences")
async def save_preferences(request: Request, values: Preferences):
    db = request.app.state.db
    for key, value in values.model_dump().items():
        db.set_setting("ux_" + key, value)
    return values.model_dump()


@router.get("/operator", response_class=HTMLResponse)
async def operator():
    from pathlib import Path
    page = Path(__file__).parent / "templates" / "operator.html"
    return HTMLResponse(page.read_text(encoding="utf-8"))


@router.get("/operator/manifest.webmanifest")
async def manifest():
    return JSONResponse({"name":"MeshWX Operator Center","short_name":"MeshWX","start_url":"/operator","display":"standalone","background_color":"#101a22","theme_color":"#101a22"},media_type="application/manifest+json")
