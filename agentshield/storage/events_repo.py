from __future__ import annotations

import json

from agentshield.core.events import AgentShieldEvent
from agentshield.storage.db import EventRecord, SessionLocal


def save_event(event: AgentShieldEvent) -> None:
    with SessionLocal() as session:
        try:
            record = EventRecord(
                event_id=event.event_id,
                created_at=event.created_at.isoformat(),
                session_id=event.session_id,
                agent_id=event.agent_id,
                agent_name=event.agent_name,
                source_layer=event.source_layer,
                event_type=event.event_type,
                action=event.action,
                summary=event.summary,
                severity=event.severity,
                verdict=event.verdict,
                blocked=event.blocked,
                decision=event.decision,
                risk_score=event.risk.risk_score,
                anomaly_score=event.risk.anomaly_score,
                trust_grade=event.risk.trust_grade,
                tags_json=json.dumps(event.tags),
                evidence_json=json.dumps([e.model_dump() for e in event.evidence]),
                raw_payload_json=json.dumps(event.raw_payload),
                anchor_goal=event.anchor_goal,
                drift_score=event.drift_score,
                watermark=event.watermark,
                pid=event.pid,
                path=event.path,
                domain=event.domain,
                tool_name=event.tool_name,
                reason=event.reason,
                matched_rules_json=json.dumps(event.policy.matched_rules),
                approval_required=event.policy.approval_required,
                approval_status=event.policy.approval_status,
                rationale=event.policy.rationale,
            )
            session.add(record)
            session.commit()
        except Exception:
            session.rollback()
            raise


def count_events() -> int:
    with SessionLocal() as session:
        return session.query(EventRecord).count()
