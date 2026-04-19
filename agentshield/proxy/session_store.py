from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class RuntimeSession:
    session_id: str
    agent_id: str = "openclaw"
    agent_name: str = "OpenClaw"
    provider: str = "google"
    model: str = "unknown"
    anchor_goal: str | None = None
    message_count: int = 0
    tool_count: int = 0
    prompt_tokens: int = 0
    candidate_tokens: int = 0
    total_tokens: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, RuntimeSession] = {}
        
    def update_usage(
        self,
        session_id: str,
        *,
        prompt_tokens: int,
        candidate_tokens: int,
        total_tokens: int,
    ) -> None:
        if session_id in self._sessions:
            s = self._sessions[session_id]
            s.prompt_tokens += prompt_tokens
            s.candidate_tokens += candidate_tokens
            s.total_tokens += total_tokens
            s.last_seen_at = datetime.now(timezone.utc)

    def get_or_create(
        self,
        session_id: str,
        *,
        agent_id: str = "openclaw",
        agent_name: str = "OpenClaw",
        provider: str = "google",
        model: str = "unknown",
    ) -> RuntimeSession:
        if session_id not in self._sessions:
            self._sessions[session_id] = RuntimeSession(
                session_id=session_id,
                agent_id=agent_id,
                agent_name=agent_name,
                provider=provider,
                model=model,
            )
        return self._sessions[session_id]

    def touch(self, session_id: str) -> None:
        if session_id in self._sessions:
            self._sessions[session_id].last_seen_at = datetime.now(timezone.utc)

    def set_anchor_goal(self, session_id: str, anchor_goal: str) -> None:
        if session_id in self._sessions:
            self._sessions[session_id].anchor_goal = anchor_goal
            self._sessions[session_id].last_seen_at = datetime.now(timezone.utc)

    def increment_message_count(self, session_id: str) -> None:
        if session_id in self._sessions:
            self._sessions[session_id].message_count += 1
            self._sessions[session_id].last_seen_at = datetime.now(timezone.utc)

    def increment_tool_count(self, session_id: str) -> None:
        if session_id in self._sessions:
            self._sessions[session_id].tool_count += 1
            self._sessions[session_id].last_seen_at = datetime.now(timezone.utc)

    def all_sessions(self) -> list[RuntimeSession]:
        return list(self._sessions.values())
