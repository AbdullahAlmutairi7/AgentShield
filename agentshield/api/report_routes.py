from __future__ import annotations

from fastapi import APIRouter

from agentshield.api.reporting_service import (
    generate_alerts_export,
    generate_dashboard_summary_report,
    generate_recent_events_export,
    generate_session_incident_report,
    generate_sessions_export,
)

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("/dashboard-summary")
def report_dashboard_summary() -> dict:
    return generate_dashboard_summary_report()


@router.post("/recent-events")
def report_recent_events(limit: int = 200) -> dict:
    return generate_recent_events_export(limit=limit)


@router.post("/alerts")
def report_alerts(limit: int = 200) -> dict:
    return generate_alerts_export(limit=limit)


@router.post("/sessions")
def report_sessions(limit: int = 200) -> dict:
    return generate_sessions_export(limit=limit)


@router.post("/session/{session_id}")
def report_session_incident(session_id: str) -> dict:
    return generate_session_incident_report(session_id=session_id)
