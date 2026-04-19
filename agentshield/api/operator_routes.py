from __future__ import annotations

from fastapi import APIRouter

from agentshield.api.operator_state import (
    clear_quarantine,
    get_action_log,
    get_session_state,
    mark_reviewed,
    quarantine_session,
)

router = APIRouter(prefix="/api/operator", tags=["operator"])


@router.get("/actions")
def operator_actions(limit: int = 50) -> list[dict]:
    return get_action_log(limit=limit)


@router.get("/session/{session_id}/state")
def operator_session_state(session_id: str) -> dict:
    return get_session_state(session_id)


@router.post("/session/{session_id}/quarantine")
def operator_quarantine(session_id: str) -> dict:
    return quarantine_session(session_id)


@router.post("/session/{session_id}/review")
def operator_review(session_id: str) -> dict:
    return mark_reviewed(session_id)


@router.post("/session/{session_id}/release")
def operator_release(session_id: str) -> dict:
    return clear_quarantine(session_id)
