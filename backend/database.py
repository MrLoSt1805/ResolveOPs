
from datetime import datetime, timezone

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./resolveops.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)

    category = Column(String(50))
    priority = Column(String(30))
    assigned_team = Column(String(100))
    confidence = Column(String(30))

    status = Column(String(50), default="Pending")
    duplicate_of = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=utc_now)
    sla_deadline = Column(DateTime, nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    incident_id = Column(
        Integer,
        ForeignKey("incidents.id"),
        nullable=False,
    )
    action = Column(String(100), nullable=False)
    details = Column(Text)
    timestamp = Column(DateTime, default=utc_now)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    incident_id = Column(
        Integer,
        ForeignKey("incidents.id"),
        nullable=False,
    )
    recipient = Column(String(255))
    status = Column(String(30), default="Pending")
    retry_count = Column(Integer, default=0)


def init_db():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("Database created successfully!")
