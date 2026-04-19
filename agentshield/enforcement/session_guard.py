from __future__ import annotations

from agentshield.api.operator_state import get_session_state


def check_session_quarantine(session_id: str) -> dict:
    state = get_session_state(session_id)

    if state["quarantined"]:
        return {
            "allowed": False,
            "decision": "quarantine",
            "blocked": True,
            "reason": "Session is quarantined by operator action",
            "matched_rules": ["operator_quarantine"],
        }

    return {
        "allowed": True,
        "decision": "observe",
        "blocked": False,
        "reason": "Session not quarantined",
        "matched_rules": [],
    }
