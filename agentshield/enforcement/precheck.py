from __future__ import annotations

from agentshield.api.operator_state import is_reviewed
from agentshield.config.settings import load_settings
from agentshield.enforcement.llm_policy_judge import (
    judge_prompt_with_gemini,
    llm_judge_threshold,
)
from agentshield.enforcement.payload_scope import build_policy_scope
from agentshield.enforcement.rule_matcher import (
    find_blocked_command_hits,
    find_blocked_domain_hits,
    find_keyword_hits,
    find_protected_path_hits,
    find_tool_hits,
)
from agentshield.enforcement.rules_loader import load_enforcement_rules
from agentshield.enforcement.session_guard import check_session_quarantine


def run_pre_policy_check(
    *,
    session_id: str,
    model: str,
    anchor_goal: str | None,
    payload: dict,
) -> dict:
    rules = load_enforcement_rules()
    settings = load_settings()

    enforce_mode = settings.policy.mode.lower() == "enforce"
    reviewed = is_reviewed(session_id)
    scoped_payload = build_policy_scope(payload)

    # 1) Highest-priority operator/session block
    quarantine_check = check_session_quarantine(session_id)
    if quarantine_check["blocked"]:
        return {
            "allowed": False if enforce_mode else True,
            "decision": "quarantine" if enforce_mode else "warn",
            "blocked": True if enforce_mode else False,
            "reason": quarantine_check["reason"] if enforce_mode else "Session is quarantined, but policy mode is observe",
            "matched_rules": quarantine_check["matched_rules"],
            "session_id": session_id,
            "model": model,
            "anchor_goal": anchor_goal,
        }

    # 2) Static hard blocks
    protected_path_hits = find_protected_path_hits(
        scoped_payload,
        rules.get("protected_paths", []),
    )
    if protected_path_hits:
        return {
            "allowed": False if enforce_mode else True,
            "decision": "deny" if enforce_mode else "warn",
            "blocked": True if enforce_mode else False,
            "reason": f"Protected path access detected: {', '.join(protected_path_hits)}",
            "matched_rules": ["protected_paths"],
            "session_id": session_id,
            "model": model,
            "anchor_goal": anchor_goal,
        }

    blocked_command_hits = find_blocked_command_hits(
        scoped_payload,
        rules.get("blocked_command_patterns", []),
    )
    if blocked_command_hits:
        return {
            "allowed": False if enforce_mode else True,
            "decision": "deny" if enforce_mode else "warn",
            "blocked": True if enforce_mode else False,
            "reason": f"Blocked command pattern detected: {', '.join(blocked_command_hits)}",
            "matched_rules": ["blocked_command_patterns"],
            "session_id": session_id,
            "model": model,
            "anchor_goal": anchor_goal,
        }

    blocked_domain_hits = find_blocked_domain_hits(
        scoped_payload,
        rules.get("blocked_domains", []),
    )
    if blocked_domain_hits:
        return {
            "allowed": False if enforce_mode else True,
            "decision": "deny" if enforce_mode else "warn",
            "blocked": True if enforce_mode else False,
            "reason": f"Blocked exfiltration domain detected: {', '.join(blocked_domain_hits)}",
            "matched_rules": ["blocked_domains"],
            "session_id": session_id,
            "model": model,
            "anchor_goal": anchor_goal,
        }

    # 3) LLM judge runs BEFORE soft warnings/approval paths
    judge = judge_prompt_with_gemini(
        payload=payload,
        session_id=session_id,
        anchor_goal=anchor_goal,
        agent_model=model,
    )

    if judge is not None:
        if judge.malicious and judge.confidence >= llm_judge_threshold():
            decision = judge.recommended_decision
            if decision not in {"deny", "require_approval", "warn"}:
                decision = "deny"

            blocked = decision == "deny" and enforce_mode
            return {
                "allowed": not blocked,
                "decision": decision,
                "blocked": blocked,
                "reason": f"LLM judge flagged request as malicious: {judge.reason}",
                "matched_rules": [f"llm_judge:{judge.category}", *judge.matched_signals],
                "session_id": session_id,
                "model": model,
                "anchor_goal": anchor_goal,
            }

        if judge.malicious and judge.confidence < llm_judge_threshold():
            return {
                "allowed": True,
                "decision": "warn",
                "blocked": False,
                "reason": f"LLM judge found suspicious prompt with lower confidence: {judge.reason}",
                "matched_rules": [f"llm_judge_low_confidence:{judge.category}", *judge.matched_signals],
                "session_id": session_id,
                "model": model,
                "anchor_goal": anchor_goal,
            }

    # 4) Static soft signals after LLM judge
    tool_hits = find_tool_hits(
        scoped_payload,
        rules.get("approval_required_tools", []),
    )
    if tool_hits:
        return {
            "allowed": True,
            "decision": "require_approval",
            "blocked": False,
            "reason": f"Approval-required tool detected: {', '.join(tool_hits)}",
            "matched_rules": ["approval_required_tools"],
            "session_id": session_id,
            "model": model,
            "anchor_goal": anchor_goal,
        }

    keyword_hits = find_keyword_hits(
        scoped_payload,
        rules.get("high_risk_keywords", []),
    )
    if keyword_hits:
        decision = "observe" if reviewed and rules.get("reviewed_session_behavior", {}).get("downgrade_warn_to_observe", False) else "warn"
        return {
            "allowed": True,
            "decision": decision,
            "blocked": False,
            "reason": f"High-risk keywords detected: {', '.join(keyword_hits)}",
            "matched_rules": ["high_risk_keywords"],
            "session_id": session_id,
            "model": model,
            "anchor_goal": anchor_goal,
        }

    # 5) Default allow
    return {
        "allowed": True,
        "decision": "observe",
        "blocked": False,
        "reason": "No enforcement rule matched",
        "matched_rules": [],
        "session_id": session_id,
        "model": model,
        "anchor_goal": anchor_goal,
    }
