from agentshield.core.events import (
    AgentShieldEvent,
    Decision,
    EventType,
    EvidenceRef,
    Severity,
    Verdict,
    make_host_event,
    make_policy_event,
    make_proxy_event,
)


def main() -> None:
    proxy_event = make_proxy_event(
        session_id="sess-001",
        event_type=EventType.TOOL_CALL,
        action="tool.call",
        summary="Agent requested shell execution",
        tool_name="exec",
        drift_score=0.14,
        raw_payload={"tool": "exec", "input": {"cmd": "ls -la"}},
    )

    host_event = make_host_event(
        session_id="sess-001",
        event_type=EventType.FILE_EVENT,
        action="file.read",
        summary="Sensitive file was accessed",
        pid=31337,
        path="/home/peter/.ssh/id_rsa",
        severity=Severity.HIGH,
        reason="Read attempt on protected SSH private key path",
    )

    policy_event = make_policy_event(
        session_id="sess-001",
        action="policy.evaluate",
        summary="Access to protected SSH key denied",
        decision=Decision.DENY,
        verdict=Verdict.BLOCKED,
        matched_rules=["deny_sensitive_ssh_paths"],
        blocked=True,
        rationale="Path matches protected secret material",
        evidence=[
            EvidenceRef(kind="path", value="/home/peter/.ssh/id_rsa", note="Protected path"),
            EvidenceRef(kind="tool", value="read_file", note="Tool attempted file access"),
        ],
    )

    print("\n--- PROXY EVENT ---")
    print(proxy_event.model_dump_json(indent=2))

    print("\n--- HOST EVENT ---")
    print(host_event.model_dump_json(indent=2))

    print("\n--- POLICY EVENT ---")
    print(policy_event.model_dump_json(indent=2))

    # strict validation sanity check
    e = AgentShieldEvent(
        session_id="sess-002",
        agent_id="agent-alpha",
        source_layer="detector",
        event_type="drift_alert",
        action="drift.detected",
        summary="Semantic drift threshold exceeded",
        severity="medium",
        verdict="suspicious",
        decision="warn",
        drift_score=0.83,
        tags=["drift", "runtime"],
    )
    print("\n--- STRICT MODEL EVENT ---")
    print(e.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
