from __future__ import annotations

from agentshield.core.events import AgentShieldEvent


def score_event_risk(event: AgentShieldEvent) -> AgentShieldEvent:
    score = 0.0
    factors: dict[str, float] = {}

    if event.blocked:
        score += 0.5
        factors["blocked_action"] = 0.5

    if event.event_type in {"policy_decision", "drift_alert"}:
        score += 0.15
        factors["security_control_event"] = 0.15

    if event.decision == "require_approval":
        score += 0.2
        factors["approval_required"] = 0.2

    if event.decision == "warn":
        score += 0.1
        factors["warning_state"] = 0.1

    if event.decision in {"deny", "kill"}:
        score += 0.25
        factors["hard_enforcement"] = 0.25

    if event.decision == "quarantine":
        score += 0.4
        factors["session_quarantine"] = 0.4

    if event.path and "/.ssh" in event.path:
        score += 0.3
        factors["ssh_secret_path"] = 0.3

    if event.path and "/.aws" in event.path:
        score += 0.25
        factors["aws_secret_path"] = 0.25

    if event.domain and ("webhook.site" in event.domain or "requestcatcher" in event.domain or "transfer.sh" in event.domain):
        score += 0.35
        factors["exfil_domain"] = 0.35

    if event.reason:
        lower_reason = event.reason.lower()
        if "private key" in lower_reason or "ssh" in lower_reason:
            score += 0.2
            factors["key_material_signal"] = 0.2
        if "approval-required" in lower_reason:
            score += 0.1
            factors["manual_gate_signal"] = 0.1

    if event.drift_score is not None:
        drift_bonus = min(event.drift_score * 0.4, 0.4)
        score += drift_bonus
        factors["drift_score"] = round(drift_bonus, 4)

    score = round(min(score, 1.0), 4)
    event.risk.risk_score = score
    event.risk.factors = factors

    if score >= 0.75:
        event.risk.trust_grade = "DANGER"
    elif score >= 0.5:
        event.risk.trust_grade = "HIGH_RISK"
    elif score >= 0.25:
        event.risk.trust_grade = "SUSPICIOUS"
    else:
        event.risk.trust_grade = "NORMAL"

    return event
