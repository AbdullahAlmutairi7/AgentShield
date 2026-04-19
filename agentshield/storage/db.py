from __future__ import annotations

from pathlib import Path

from sqlalchemy import Boolean, Column, Float, Integer, String, Text, create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker


BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_DB_PATH = BASE_DIR / "agentshield.db"

engine = create_engine(
    f"sqlite:///{DEFAULT_DB_PATH}",
    future=True,
    connect_args={
        "check_same_thread": False,
        "timeout": 30,
    },
)

SessionLocal = sessionmaker(
    bind=engine,
    future=True,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)

Base = declarative_base()


class EventRecord(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String, nullable=False, unique=True, index=True)
    created_at = Column(String, nullable=False, index=True)
    session_id = Column(String, nullable=False, index=True)
    agent_id = Column(String, nullable=False, index=True)
    agent_name = Column(String, nullable=True)

    source_layer = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)

    action = Column(String, nullable=False)
    summary = Column(Text, nullable=False)

    severity = Column(String, nullable=False, index=True)
    verdict = Column(String, nullable=False, index=True)
    blocked = Column(Boolean, default=False, index=True)
    decision = Column(String, nullable=False, index=True)

    risk_score = Column(Float, default=0.0)
    anomaly_score = Column(Float, default=0.0)
    trust_grade = Column(String, nullable=True)

    tags_json = Column(Text, nullable=False, default="[]")
    evidence_json = Column(Text, nullable=False, default="[]")
    raw_payload_json = Column(Text, nullable=False, default="{}")

    anchor_goal = Column(Text, nullable=True)
    drift_score = Column(Float, nullable=True)
    watermark = Column(Integer, nullable=True)

    pid = Column(Integer, nullable=True)
    path = Column(Text, nullable=True)
    domain = Column(Text, nullable=True)
    tool_name = Column(Text, nullable=True)

    reason = Column(Text, nullable=True)
    matched_rules_json = Column(Text, nullable=False, default="[]")
    approval_required = Column(Boolean, default=False)
    approval_status = Column(String, nullable=False, default="not_required")
    rationale = Column(Text, nullable=True)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=NORMAL;")
    cursor.execute("PRAGMA busy_timeout=30000;")
    cursor.close()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
