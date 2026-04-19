from agentshield.core.events import (
    Decision,
    EventType,
    EvidenceRef,
    Severity,
    Verdict,
    make_host_event,
    make_policy_event,
    make_proxy_event,
)
from agentshield.storage.events_repo import save_event


def main() -> None:
    events = [
        make_proxy_event(
            session_id="sess-agent-001",
            event_type=EventType.LLM_REQUEST,
            action="llm.request",
            summary="User asked agent to summarize a Python file",
            raw_payload={"model": "google/gemini-2.5-flash-lite"},
        ),
        make_proxy_event(
            session_id="sess-agent-001",
            event_type=EventType.TOOL_CALL,
            action="tool.call",
            summary="Agent requested file read",
            tool_name="read_file",
            raw_payload={"path": "/home/peter/project/app.py"},
        ),
        make_host_event(
            session_id="sess-agent-001",
            event_type=EventType.FILE_EVENT,
            action="file.read",
            summary="Project file accessed",
            path="/home/peter/project/app.py",
            severity=Severity.LOW,
            reason="Normal project file access",
        ),
        make_proxy_event(
            session_id="sess-agent-002",
            event_type=EventType.TOOL_CALL,
            action="tool.call",
            summary="Agent attempted to read SSH private key",
            tool_name="read_file",
            raw_payload={"path": "/home/peter/.ssh/id_rsa"},
        ),
        make_host_event(
            session_id="sess-agent-002",
            event_type=EventType.FILE_EVENT,
            action="file.read",
            summary="Sensitive SSH key path accessed",
            path="/home/peter/.ssh/id_rsa",
            severity=Severity.HIGH,
            reason="Protected secret material path",
        ),
        make_policy_event(
            session_id="sess-agent-002",
            action="policy.evaluate",
            summary="Denied SSH key access",
            decision=Decision.DENY,
            verdict=Verdict.BLOCKED,
            matched_rules=["deny_sensitive_ssh_paths"],
            blocked=True,
            rationale="Path matches protected SSH secret rule",
            evidence=[
                EvidenceRef(kind="path", value="/home/peter/.ssh/id_rsa", note="Sensitive key path"),
                EvidenceRef(kind="tool", value="read_file", note="Tool attempted protected read"),
            ],
        ),
        make_proxy_event(
            session_id="sess-agent-003",
            event_type=EventType.DRIFT_ALERT,
            action="drift.detected",
            summary="Prompt drift exceeded threshold after tool output",
            drift_score=0.88,
            raw_payload={"anchor_goal": "summarize docs", "current_intent": "find secrets"},
        ),
        make_policy_event(
            session_id="sess-agent-003",
            action="policy.evaluate",
            summary="Issued warning for prompt drift",
            decision=Decision.WARN,
            verdict=Verdict.SUSPICIOUS,
            matched_rules=["warn_on_high_drift"],
            blocked=False,
            rationale="Drift score exceeded configured warning threshold",
        ),
    ]

    for event in events:
        save_event(event)

    print(f"Inserted {len(events)} sample events.")


if __name__ == "__main__":
    main()
