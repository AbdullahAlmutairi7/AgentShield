from __future__ import annotations

from agentshield.api.operator_state import get_session_state
from agentshield.storage.query_service import (
    get_alert_feed,
    get_event_counts,
    get_events_for_session,
    get_recent_events,
    get_session_summaries,
)


def get_dashboard_summary() -> dict:
    counts = get_event_counts()
    sessions = get_session_summaries()
    alerts = get_alert_feed(limit=10)

    high_risk_sessions = 0
    blocked_sessions = 0
    max_risk_score = 0.0

    for session in sessions:
        if session.get("blocked_count", 0) > 0:
            blocked_sessions += 1
        if session.get("max_risk_score", 0.0) >= 0.5:
            high_risk_sessions += 1
        max_risk_score = max(max_risk_score, session.get("max_risk_score", 0.0))

    top_risky = sorted(
        sessions,
        key=lambda s: (s.get("max_risk_score", 0.0), s.get("blocked_count", 0)),
        reverse=True,
    )[:5]

    top_blocked = sorted(
        [s for s in sessions if s.get("blocked_count", 0) > 0],
        key=lambda s: s.get("blocked_count", 0),
        reverse=True,
    )[:5]

    return {
        "totals": {
            "events": counts["total_events"],
            "blocked_events": counts["blocked_events"],
            "sessions": len(sessions),
            "high_risk_sessions": high_risk_sessions,
            "blocked_sessions": blocked_sessions,
            "alerts": len(alerts),
            "max_risk_score": round(max_risk_score, 4),
        },
        "breakdowns": {
            "by_severity": counts["by_severity"],
            "by_event_type": counts["by_event_type"],
            "by_source_layer": counts["by_source_layer"],
        },
        "top_risky_sessions": top_risky,
        "top_blocked_sessions": top_blocked,
    }


def get_dashboard_recent_events(limit: int = 20) -> list[dict]:
    return get_recent_events(limit=limit)


def get_dashboard_sessions(limit: int = 20) -> list[dict]:
    sessions = get_session_summaries()[:limit]

    enriched = []
    for session in sessions:
        state = get_session_state(session["session_id"])
        enriched.append({
            **session,
            "quarantined": state["quarantined"],
            "reviewed": state["reviewed"],
        })

    return enriched


def get_dashboard_alerts(limit: int = 20) -> list[dict]:
    return get_alert_feed(limit=limit)


def get_dashboard_session_detail(session_id: str) -> dict:
    sessions = get_session_summaries()
    session_info = next((s for s in sessions if s["session_id"] == session_id), None)
    events = get_events_for_session(session_id=session_id, limit=200)

    if session_info:
        session_info = {
            **session_info,
            **get_session_state(session_id),
        }

    return {
        "session": session_info,
        "events": events,
    }
