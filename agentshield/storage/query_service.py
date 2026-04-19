from __future__ import annotations

import json
from collections import Counter, defaultdict

from agentshield.storage.db import EventRecord, SessionLocal


def get_recent_events(limit: int = 20) -> list[dict]:
    with SessionLocal() as session:
        rows = (
            session.query(EventRecord)
            .order_by(EventRecord.id.desc())
            .limit(limit)
            .all()
        )

        results: list[dict] = []
        for row in rows:
            results.append(
                {
                    "event_id": row.event_id,
                    "created_at": row.created_at,
                    "session_id": row.session_id,
                    "agent_id": row.agent_id,
                    "agent_name": row.agent_name,
                    "source_layer": row.source_layer,
                    "event_type": row.event_type,
                    "action": row.action,
                    "summary": row.summary,
                    "severity": row.severity,
                    "verdict": row.verdict,
                    "blocked": row.blocked,
                    "decision": row.decision,
                    "risk_score": row.risk_score,
                    "anomaly_score": row.anomaly_score,
                    "trust_grade": row.trust_grade,
                    "tags": json.loads(row.tags_json or "[]"),
                    "matched_rules": json.loads(row.matched_rules_json or "[]"),
                    "path": row.path,
                    "domain": row.domain,
                    "tool_name": row.tool_name,
                    "reason": row.reason,
                }
            )
        return results


def get_event_counts() -> dict:
    with SessionLocal() as session:
        rows = session.query(EventRecord).all()

    severity_counter = Counter()
    event_type_counter = Counter()
    source_counter = Counter()
    blocked_count = 0

    for row in rows:
        severity_counter[row.severity] += 1
        event_type_counter[row.event_type] += 1
        source_counter[row.source_layer] += 1
        if row.blocked:
            blocked_count += 1

    return {
        "total_events": len(rows),
        "blocked_events": blocked_count,
        "by_severity": dict(severity_counter),
        "by_event_type": dict(event_type_counter),
        "by_source_layer": dict(source_counter),
    }


def get_session_summaries() -> list[dict]:
    with SessionLocal() as session:
        rows = (
            session.query(EventRecord)
            .order_by(EventRecord.id.asc())
            .all()
        )

    sessions: dict[str, dict] = {}
    for row in rows:
        if row.session_id not in sessions:
            sessions[row.session_id] = {
                "session_id": row.session_id,
                "agent_id": row.agent_id,
                "agent_name": row.agent_name,
                "event_count": 0,
                "blocked_count": 0,
                "max_risk_score": 0.0,
                "max_anomaly_score": 0.0,
                "max_drift_score": 0.0,
                "max_trust_grade": None,
                "severities": Counter(),
                "event_types": Counter(),
                "started_at": row.created_at,
                "last_seen_at": row.created_at,
            }

        s = sessions[row.session_id]
        s["event_count"] += 1
        s["last_seen_at"] = row.created_at
        s["severities"][row.severity] += 1
        s["event_types"][row.event_type] += 1
        s["max_risk_score"] = max(s["max_risk_score"], row.risk_score or 0.0)
        s["max_anomaly_score"] = max(s["max_anomaly_score"], row.anomaly_score or 0.0)
        s["max_drift_score"] = max(s["max_drift_score"], row.drift_score or 0.0)
        
        if row.trust_grade:
            current_rank = {"NORMAL": 1, "SUSPICIOUS": 2, "HIGH_RISK": 3, "DANGER": 4}
            existing = s["max_trust_grade"]
            if existing is None or current_rank.get(row.trust_grade, 0) > current_rank.get(existing, 0):
                s["max_trust_grade"] = row.trust_grade

        if row.blocked:
            s["blocked_count"] += 1

    output: list[dict] = []
    for session_id, data in sessions.items():
        output.append(
            {
                **data,
                "severities": dict(data["severities"]),
                "event_types": dict(data["event_types"]),
            }
        )

    output.sort(key=lambda x: x["last_seen_at"], reverse=True)
    return output


def get_alert_feed(limit: int = 20) -> list[dict]:
    with SessionLocal() as session:
        rows = (
            session.query(EventRecord)
            .filter(EventRecord.severity.in_(["high", "critical"]))
            .order_by(EventRecord.id.desc())
            .limit(limit)
            .all()
        )

    feed: list[dict] = []
    for row in rows:
        feed.append(
            {
                "created_at": row.created_at,
                "session_id": row.session_id,
                "event_type": row.event_type,
                "summary": row.summary,
                "severity": row.severity,
                "blocked": row.blocked,
                "reason": row.reason,
            }
        )
    return feed
    
def get_events_for_session(session_id: str, limit: int = 100) -> list[dict]:
    with SessionLocal() as session:
        rows = (
            session.query(EventRecord)
            .filter(EventRecord.session_id == session_id)
            .order_by(EventRecord.id.asc())
            .limit(limit)
            .all()
        )

        results: list[dict] = []
        for row in rows:
            results.append(
                {
                    "event_id": row.event_id,
                    "created_at": row.created_at,
                    "session_id": row.session_id,
                    "agent_id": row.agent_id,
                    "agent_name": row.agent_name,
                    "source_layer": row.source_layer,
                    "event_type": row.event_type,
                    "action": row.action,
                    "summary": row.summary,
                    "severity": row.severity,
                    "verdict": row.verdict,
                    "blocked": row.blocked,
                    "decision": row.decision,
                    "risk_score": row.risk_score,
                    "anomaly_score": row.anomaly_score,
                    "trust_grade": row.trust_grade,
                    "tags": json.loads(row.tags_json or "[]"),
                    "matched_rules": json.loads(row.matched_rules_json or "[]"),
                    "path": row.path,
                    "domain": row.domain,
                    "tool_name": row.tool_name,
                    "reason": row.reason,
                    "anchor_goal": row.anchor_goal,
                    "drift_score": row.drift_score,
                }
            )
        return results
