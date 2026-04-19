from __future__ import annotations

from fastapi import APIRouter

from agentshield.api.dashboard_service import (
    get_dashboard_alerts,
    get_dashboard_recent_events,
    get_dashboard_session_detail,
    get_dashboard_sessions,
    get_dashboard_summary,
)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary")
def dashboard_summary() -> dict:
    return get_dashboard_summary()


@router.get("/recent-events")
def dashboard_recent_events(limit: int = 20) -> list[dict]:
    return get_dashboard_recent_events(limit=limit)


@router.get("/sessions")
def dashboard_sessions(limit: int = 20) -> list[dict]:
    return get_dashboard_sessions(limit=limit)


@router.get("/alerts")
def dashboard_alerts(limit: int = 20) -> list[dict]:
    return get_dashboard_alerts(limit=limit)
    
@router.get("/session/{session_id}")
def dashboard_session_detail(session_id: str) -> dict:
    return get_dashboard_session_detail(session_id=session_id)
