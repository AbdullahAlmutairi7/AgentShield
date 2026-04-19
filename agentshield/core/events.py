from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, ConfigDict


# -----------------------------
# Core enums
# -----------------------------

class SourceLayer(str, Enum):
    PROXY = "proxy"
    DETECTOR = "detector"
    COLLECTOR = "collector"
    POLICY = "policy"
    UI = "ui"
    SYSTEM = "system"


class EventType(str, Enum):
    # Runtime / proxy
    LLM_REQUEST = "llm_request"
    LLM_RESPONSE = "llm_response"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    SESSION_START = "session_start"
    SESSION_END = "session_end"

    # Detection / analysis
    DRIFT_ALERT = "drift_alert"
    LOOP_ALERT = "loop_alert"
    INJECTION_ALERT = "injection_alert"
    SECRET_ALERT = "secret_alert"
    ANOMALY_ALERT = "anomaly_alert"

    # Host telemetry (Aegis-inspired)
    PROCESS_EVENT = "process_event"
    FILE_EVENT = "file_event"
    NETWORK_EVENT = "network_event"
    CONFIG_ACCESS = "config_access"

    # Enforcement / policy
    POLICY_DECISION = "policy_decision"
    APPROVAL_REQUEST = "approval_request"
    APPROVAL_RESULT = "approval_result"
    INTERVENTION = "intervention"
    QUARANTINE_EVENT = "quarantine_event"

    # Audit / reporting
    AUDIT_EVENT = "audit_event"
    STATUS_EVENT = "status_event"


class Severity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Decision(str, Enum):
    OBSERVE = "observe"
    ALLOW = "allow"
    WARN = "warn"
    CLEAN = "clean"
    REDACT = "redact"
    REQUIRE_APPROVAL = "require_approval"
    DENY = "deny"
    KILL = "kill"
    QUARANTINE = "quarantine"


class Verdict(str, Enum):
    PASS = "pass"
    SUSPICIOUS = "suspicious"
    BLOCKED = "blocked"
    MODIFIED = "modified"
    QUARANTINED = "quarantined"


# -----------------------------
# Structured evidence models
# -----------------------------

class EvidenceRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["text", "path", "domain", "pid", "tool", "payload", "rule", "session", "agent"]
    value: str
    note: str | None = None


class RiskSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    risk_score: float = 0.0
    anomaly_score: float = 0.0
    trust_grade: str | None = None
    factors: dict[str, float] = Field(default_factory=dict)


class PolicyTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    matched_rules: list[str] = Field(default_factory=list)
    decision: Decision = Decision.OBSERVE
    rationale: str | None = None
    approval_required: bool = False
    approval_status: Literal["not_required", "pending", "approved", "denied"] = "not_required"


# -----------------------------
# Canonical AgentShield event
# -----------------------------

class AgentShieldEvent(BaseModel):
    """
    One normalized event object for:
    - Aegis-style host telemetry
    - AegisSync-style proxy/runtime judgments
    - AgentShield policy enforcement actions
    """

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Session / identity
    session_id: str
    agent_id: str = "unknown_agent"
    agent_name: str | None = None
    source_layer: SourceLayer
    event_type: EventType

    # Main action summary
    action: str
    summary: str

    # Security posture
    severity: Severity = Severity.INFO
    verdict: Verdict = Verdict.PASS
    blocked: bool = False
    decision: Decision = Decision.OBSERVE

    # Policy / scoring
    risk: RiskSnapshot = Field(default_factory=RiskSnapshot)
    policy: PolicyTrace = Field(default_factory=PolicyTrace)

    # Correlation & UI support
    tags: list[str] = Field(default_factory=list)
    anchor_goal: str | None = None
    drift_score: float | None = None
    watermark: int | None = None

    # Evidence
    evidence: list[EvidenceRef] = Field(default_factory=list)

    # Raw data for later auditing / replay
    raw_payload: dict[str, Any] = Field(default_factory=dict)

    # Optional host/runtime-specific fields
    pid: int | None = None
    path: str | None = None
    domain: str | None = None
    tool_name: str | None = None

    # Human-readable explanation
    reason: str | None = None


# -----------------------------
# Convenience constructors
# -----------------------------

def make_proxy_event(
    *,
    session_id: str,
    action: str,
    summary: str,
    event_type: EventType,
    agent_id: str = "openclaw",
    agent_name: str | None = "OpenClaw",
    tool_name: str | None = None,
    drift_score: float | None = None,
    raw_payload: dict[str, Any] | None = None,
) -> AgentShieldEvent:
    return AgentShieldEvent(
        session_id=session_id,
        agent_id=agent_id,
        agent_name=agent_name,
        source_layer=SourceLayer.PROXY,
        event_type=event_type,
        action=action,
        summary=summary,
        tool_name=tool_name,
        drift_score=drift_score,
        raw_payload=raw_payload or {},
        tags=["proxy"],
    )


def make_host_event(
    *,
    session_id: str,
    event_type: EventType,
    action: str,
    summary: str,
    pid: int | None = None,
    path: str | None = None,
    domain: str | None = None,
    severity: Severity = Severity.MEDIUM,
    reason: str | None = None,
) -> AgentShieldEvent:
    tags = ["host", event_type.value]
    return AgentShieldEvent(
        session_id=session_id,
        source_layer=SourceLayer.COLLECTOR,
        event_type=event_type,
        action=action,
        summary=summary,
        pid=pid,
        path=path,
        domain=domain,
        severity=severity,
        reason=reason,
        tags=tags,
    )


def make_policy_event(
    *,
    session_id: str,
    action: str,
    summary: str,
    decision: Decision,
    verdict: Verdict,
    matched_rules: list[str],
    blocked: bool,
    rationale: str,
    evidence: list[EvidenceRef] | None = None,
) -> AgentShieldEvent:
    return AgentShieldEvent(
        session_id=session_id,
        source_layer=SourceLayer.POLICY,
        event_type=EventType.POLICY_DECISION,
        action=action,
        summary=summary,
        decision=decision,
        verdict=verdict,
        blocked=blocked,
        evidence=evidence or [],
        policy=PolicyTrace(
            matched_rules=matched_rules,
            decision=decision,
            rationale=rationale,
            approval_required=(decision == Decision.REQUIRE_APPROVAL),
            approval_status="pending" if decision == Decision.REQUIRE_APPROVAL else "not_required",
        ),
        severity=Severity.HIGH if blocked else Severity.MEDIUM,
        tags=["policy", decision.value],
        reason=rationale,
    )
