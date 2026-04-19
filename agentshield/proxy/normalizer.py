from __future__ import annotations

from typing import Any
from uuid import uuid4


def normalize_model_name(model: str) -> str:
    """
    Convert names like:
      google/gemini-2.5-flash-lite -> gemini-2.5-flash-lite
    """
    value = model.strip()
    if "/" in value:
        value = value.split("/")[-1]
    return value


def extract_session_id(payload: dict[str, Any]) -> str:
    candidates = [
        payload.get("session_id"),
        payload.get("conversation_id"),
        payload.get("thread_id"),
        payload.get("metadata", {}).get("session_id") if isinstance(payload.get("metadata"), dict) else None,
        payload.get("metadata", {}).get("conversation_id") if isinstance(payload.get("metadata"), dict) else None,
    ]
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return f"sess-{uuid4()}"


def extract_model(payload: dict[str, Any], default_model: str) -> str:
    model = payload.get("model")
    if isinstance(model, str) and model.strip():
        return normalize_model_name(model)
    return normalize_model_name(default_model)


def extract_anchor_goal(payload: dict[str, Any]) -> str | None:
    messages = payload.get("messages", [])
    if isinstance(messages, list):
        for msg in messages:
            if not isinstance(msg, dict):
                continue
            if msg.get("role") == "user":
                content = msg.get("content")
                if isinstance(content, str) and content.strip():
                    return content.strip()[:500]
                if isinstance(content, list):
                    fragments: list[str] = []
                    for part in content:
                        if isinstance(part, dict):
                            text = part.get("text")
                            if isinstance(text, str) and text.strip():
                                fragments.append(text.strip())
                    if fragments:
                        return " ".join(fragments)[:500]

    contents = payload.get("contents", [])
    if isinstance(contents, list):
        for item in contents:
            if not isinstance(item, dict):
                continue
            if item.get("role") == "user":
                parts = item.get("parts", [])
                if isinstance(parts, list):
                    fragments: list[str] = []
                    for part in parts:
                        if isinstance(part, dict):
                            text = part.get("text")
                            if isinstance(text, str) and text.strip():
                                fragments.append(text.strip())
                    if fragments:
                        return " ".join(fragments)[:500]
    return None


def extract_message_count(payload: dict[str, Any]) -> int:
    if isinstance(payload.get("messages"), list):
        return len(payload["messages"])
    if isinstance(payload.get("contents"), list):
        return len(payload["contents"])
    return 0


def extract_tool_calls(payload: dict[str, Any]) -> list[dict[str, Any]]:
    tool_calls: list[dict[str, Any]] = []

    if isinstance(payload.get("tool_calls"), list):
        for item in payload["tool_calls"]:
            if isinstance(item, dict):
                tool_calls.append(item)

    if isinstance(payload.get("tools"), list):
        for item in payload["tools"]:
            if isinstance(item, dict):
                tool_calls.append(item)

    return tool_calls
