from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


ACTION_LOG: list[dict[str, Any]] = []
QUARANTINED_SESSIONS: set[str] = set()
REVIEWED_SESSIONS: set[str] = set()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def log_action(action_type: str, session_id: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    entry = {
        "timestamp": now_iso(),
        "action_type": action_type,
        "session_id": session_id,
        "details": details or {},
    }
    ACTION_LOG.insert(0, entry)
    return entry


def quarantine_session(session_id: str) -> dict[str, Any]:
    QUARANTINED_SESSIONS.add(session_id)
    return log_action("quarantine", session_id, {"state": "quarantined"})


def mark_reviewed(session_id: str) -> dict[str, Any]:
    REVIEWED_SESSIONS.add(session_id)
    return log_action("reviewed", session_id, {"state": "reviewed"})


def clear_quarantine(session_id: str) -> dict[str, Any]:
    QUARANTINED_SESSIONS.discard(session_id)
    return log_action("clear_quarantine", session_id, {"state": "released"})


def get_action_log(limit: int = 50) -> list[dict[str, Any]]:
    return ACTION_LOG[:limit]


def get_session_state(session_id: str) -> dict[str, bool]:
    return {
        "quarantined": session_id in QUARANTINED_SESSIONS,
        "reviewed": session_id in REVIEWED_SESSIONS,
    }

def is_reviewed(session_id: str) -> bool:
    return session_id in REVIEWED_SESSIONS
