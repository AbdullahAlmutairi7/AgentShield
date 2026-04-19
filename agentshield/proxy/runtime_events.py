from __future__ import annotations

from typing import Any

from agentshield.core.events import EventType, make_proxy_event
from agentshield.storage.events_repo import save_event


def emit_llm_request_event(
    *,
    session_id: str,
    model: str,
    anchor_goal: str | None,
    payload: dict[str, Any],
) -> None:
    event = make_proxy_event(
        session_id=session_id,
        event_type=EventType.LLM_REQUEST,
        action="llm.request",
        summary="LLM request observed by AgentShield proxy",
        raw_payload={
            "model": model,
            "message_count": len(payload.get("messages", [])) if isinstance(payload.get("messages"), list) else 0,
        },
    )
    event.anchor_goal = anchor_goal
    event.tags.extend(["runtime", "llm_request"])
    save_event(event)


def emit_tool_call_event(
    *,
    session_id: str,
    tool_name: str,
    tool_payload: dict[str, Any],
) -> None:
    event = make_proxy_event(
        session_id=session_id,
        event_type=EventType.TOOL_CALL,
        action="tool.call",
        summary=f"Tool call observed: {tool_name}",
        tool_name=tool_name,
        raw_payload=tool_payload,
    )
    event.tags.extend(["runtime", "tool_call"])
    save_event(event)


def emit_llm_response_event(
    *,
    session_id: str,
    model: str,
    response_preview: str,
) -> None:
    event = make_proxy_event(
        session_id=session_id,
        event_type=EventType.LLM_RESPONSE,
        action="llm.response",
        summary="LLM response observed by AgentShield proxy",
        raw_payload={
            "model": model,
            "preview": response_preview[:300],
        },
    )
    event.tags.extend(["runtime", "llm_response"])
    save_event(event)
    
def emit_drift_alert_event(
    *,
    session_id: str,
    drift_score: float,
    anchor_goal: str | None,
    current_text: str,
) -> None:
    from agentshield.core.events import EventType, Severity, Verdict, make_proxy_event
    from agentshield.detectors.risk_engine import score_event_risk

    event = make_proxy_event(
        session_id=session_id,
        event_type=EventType.DRIFT_ALERT,
        action="drift.detected",
        summary="Semantic drift detected between anchor goal and current request",
        drift_score=drift_score,
        raw_payload={
            "anchor_goal": anchor_goal,
            "current_text": current_text[:500],
        },
    )

    event.verdict = Verdict.SUSPICIOUS
    event.severity = Severity.MEDIUM if drift_score < 0.75 else Severity.HIGH
    event.anchor_goal = anchor_goal
    event.tags.extend(["runtime", "drift"])
    score_event_risk(event)
    save_event(event)
    
    
def emit_policy_check_event(
    *,
    session_id: str,
    decision: str,
    blocked: bool,
    reason: str,
    matched_rules: list[str],
) -> None:
    from agentshield.core.events import (
        Decision,
        EvidenceRef,
        Verdict,
        make_policy_event,
    )
    from agentshield.detectors.risk_engine import score_event_risk

    decision_map = {
        "observe": Decision.OBSERVE,
        "allow": Decision.ALLOW,
        "warn": Decision.WARN,
        "clean": Decision.CLEAN,
        "redact": Decision.REDACT,
        "require_approval": Decision.REQUIRE_APPROVAL,
        "deny": Decision.DENY,
        "kill": Decision.KILL,
        "quarantine": Decision.QUARANTINE,
    }

    if blocked:
        verdict = Verdict.BLOCKED
    elif decision in {"warn", "require_approval"}:
        verdict = Verdict.SUSPICIOUS
    else:
        verdict = Verdict.PASS

    event = make_policy_event(
        session_id=session_id,
        action="policy.precheck",
        summary="Pre-policy check completed",
        decision=decision_map.get(decision, Decision.OBSERVE),
        verdict=verdict,
        matched_rules=matched_rules,
        blocked=blocked,
        rationale=reason,
        evidence=[
            EvidenceRef(kind="session", value=session_id, note="Proxy session under evaluation"),
        ],
    )
    
    if decision == "warn":
        event.summary = "Policy warning issued"
    elif decision == "require_approval":
        event.summary = "Approval-required action detected"
    elif decision == "quarantine":
        event.summary = "Quarantined session blocked at proxy"
    elif blocked:
        event.summary = "Policy blocked request"

    if decision == "quarantine":
        event.severity = "critical"
    elif blocked:
        event.severity = "high"
    elif decision in {"warn", "require_approval"}:
        event.severity = "medium"
    else:
        event.severity = "info"
    
    event.tags.extend(["runtime", "policy_precheck"])
    score_event_risk(event)
    save_event(event)
