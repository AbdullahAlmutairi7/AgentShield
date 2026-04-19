from __future__ import annotations

from typing import Any


INTERNAL_FIELDS = {
    "session_id",
    "conversation_id",
    "thread_id",
    "agentshield_meta",
    "agent_id",
    "agent_name",
}


def split_internal_metadata(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Returns:
      forward_payload: safe Gemini-facing payload
      internal_meta: AgentShield-only fields
    """
    forward_payload = dict(payload)
    internal_meta: dict[str, Any] = {}

    for key in list(INTERNAL_FIELDS):
        if key in forward_payload:
            internal_meta[key] = forward_payload.pop(key)

    return forward_payload, internal_meta
