
from fastapi import FastAPI, HTTPException, Depends
from contextlib import asynccontextmanager
from backend.rules import calculate_sla
from backend.scheduler import start_scheduler, stop_scheduler
from backend.security import verify_api_key
from pydantic import BaseModel, Field, EmailStr
from backend.database import (
    SessionLocal,
    Incident,
    AuditLog,
    init_db,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()

    try:
        yield
    finally:
        stop_scheduler()


app = FastAPI(
    title="ResolveOps API",
    description="AI-Powered IT Incident RPA System",
    version="1.0",
    dependencies=[Depends(verify_api_key)],
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan,
)

init_db()


class IncidentCreate(BaseModel):
    name: str = Field(min_length=2)
    email: EmailStr
    title: str = Field(min_length=3)
    description: str = Field(min_length=10)


@app.get("/")
def home():
    return {
        "message": "ResolveOps API is running",
        "status": "healthy",
    }


@app.post("/incidents")
def create_incident(data: IncidentCreate):
    db = SessionLocal()

    try:
        incident = Incident(
            name=data.name,
            email=str(data.email),
            title=data.title,
            description=data.description,
            status="Pending",
        )

        db.add(incident)
        db.flush()

        db.add(
            AuditLog(
                incident_id=incident.id,
                action="INCIDENT_CREATED",
                details="New incident submitted",
            )
        )

        db.commit()
        db.refresh(incident)

        return {
            "message": "Incident created",
            "incident_id": incident.id,
            "status": incident.status,
        }

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@app.get("/incidents")
def list_incidents():
    db = SessionLocal()

    try:
        incidents = db.query(Incident).order_by(
            Incident.id.desc()
        ).all()

        return [
            {
                "id": i.id,
                "title": i.title,
                "description": i.description,
                "category": i.category,
                "priority": i.priority,
                "status": i.status,
                "assigned_team": i.assigned_team,
            }
            for i in incidents
        ]

    finally:
        db.close()


@app.get("/incidents/pending")
def pending_incidents():
    db = SessionLocal()

    try:
        incidents = db.query(Incident).filter(
            Incident.status == "Pending"
        ).all()

        return [
            {
                "id": i.id,
                "title": i.title,
                "description": i.description,
            }
            for i in incidents
        ]

    finally:
        db.close()


@app.get("/incidents/{incident_id}/audit")
def get_audit_logs(incident_id: int):
    db = SessionLocal()

    try:
        incident = db.get(Incident, incident_id)

        if incident is None:
            raise HTTPException(
                status_code=404,
                detail="Incident not found",
            )

        logs = db.query(AuditLog).filter(
            AuditLog.incident_id == incident_id
        ).order_by(AuditLog.id).all()

        return [
            {
                "action": log.action,
                "details": log.details,
                "timestamp": log.timestamp,
            }
            for log in logs
        ]

    finally:
        db.close()


from backend.processor import process_incident


@app.post("/incidents/{incident_id}/process")
def process_incident_endpoint(incident_id: int):
    try:
        result = process_incident(incident_id)
        return result

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Incident processing failed"
        )


# ---------- Human-in-the-loop review ----------

from typing import Literal


class IncidentReview(BaseModel):
    reviewer: str = Field(min_length=2, max_length=100)
    decision: Literal["approve", "override"]
    category: str | None = None
    priority: Literal["Low", "Medium", "High", "Critical"] | None = None
    assigned_team: str | None = None
    notes: str = Field(default="", max_length=1000)


@app.get("/incidents/review")
def get_review_queue():
    db = SessionLocal()

    try:
        incidents = (
            db.query(Incident)
            .filter(Incident.status == "Review Required")
            .order_by(Incident.id.desc())
            .all()
        )

        return [
            {
                "id": i.id,
                "title": i.title,
                "description": i.description,
                "category": i.category,
                "priority": i.priority,
                "assigned_team": i.assigned_team,
                "status": i.status,
            }
            for i in incidents
        ]

    finally:
        db.close()



@app.post("/incidents/{incident_id}/review")
def review_incident(incident_id: int, data: IncidentReview):
    db = SessionLocal()

    try:
        incident = db.get(Incident, incident_id)

        if incident is None:
            raise HTTPException(
                status_code=404,
                detail="Incident not found",
            )

        if incident.status != "Review Required":
            raise HTTPException(
                status_code=409,
                detail="Only incidents requiring review can be approved.",
            )

        # Save original values before any override.
        old_priority = incident.priority
        old_sla_deadline = incident.sla_deadline

        if data.decision == "override":
            if not all([
                data.category and data.category.strip(),
                data.priority,
                data.assigned_team and data.assigned_team.strip(),
            ]):
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "An override requires category, priority "
                        "and assigned_team."
                    ),
                )

            incident.category = data.category.strip()
            incident.priority = data.priority
            incident.assigned_team = data.assigned_team.strip()
            audit_action = "HUMAN_OVERRIDE"

            # Update SLA when the reviewer changes priority.
            if incident.priority != old_priority:
                incident.sla_deadline = calculate_sla(
                    incident.priority
                )["sla_deadline"]

                db.add(
                    AuditLog(
                        incident_id=incident.id,
                        action="SLA_RECALCULATED",
                        details=(
                            f"Reviewer: {data.reviewer.strip()} | "
                            f"Old priority: {old_priority} | "
                            f"New priority: {incident.priority} | "
                            f"Old deadline: {old_sla_deadline} | "
                            f"New deadline: {incident.sla_deadline}"
                        ),
                    )
                )

        else:
            if not all([
                incident.category,
                incident.priority,
                incident.assigned_team,
            ]):
                raise HTTPException(
                    status_code=422,
                    detail="AI results are incomplete. Use override instead.",
                )

            audit_action = "HUMAN_APPROVED"

        incident.status = "Open"

        db.add(
            AuditLog(
                incident_id=incident.id,
                action=audit_action,
                details=(
                    f"Reviewer: {data.reviewer.strip()} | "
                    f"Decision: {data.decision} | "
                    f"Category: {incident.category} | "
                    f"Priority: {incident.priority} | "
                    f"Team: {incident.assigned_team} | "
                    f"Notes: {data.notes}"
                ),
            )
        )

        db.commit()
        db.refresh(incident)

        return {
            "message": "Human review completed",
            "incident_id": incident.id,
            "decision": data.decision,
            "status": incident.status,
            "category": incident.category,
            "priority": incident.priority,
            "assigned_team": incident.assigned_team,
            "sla_deadline": (
                incident.sla_deadline.isoformat()
                if incident.sla_deadline
                else None
            ),
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()



# ---------- SLA Monitoring ----------

from backend.sla_monitor import check_sla


@app.post("/sla/check")
def check_sla_endpoint():
    try:
        return check_sla()

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="SLA monitoring failed",
        )

# ---------- Scheduler Status ----------

from backend.scheduler import scheduler


@app.get("/scheduler/status")
def scheduler_status():
    jobs = scheduler.get_jobs()

    return {
        "scheduler_running": scheduler.running,
        "job_count": len(jobs),
        "jobs": [
            {
                "id": job.id,
                "next_run_time": (
                    job.next_run_time.isoformat()
                    if job.next_run_time
                    else None
                ),
            }
            for job in jobs
        ],
    }


# ---------- Notification Queue ----------

from backend.database import Notification


@app.get("/notifications")
def list_notifications():
    db = SessionLocal()

    try:
        notifications = (
            db.query(Notification)
            .order_by(Notification.id.desc())
            .all()
        )

        return [
            {
                "id": item.id,
                "incident_id": item.incident_id,
                "recipient": item.recipient,
                "status": item.status,
                "retry_count": item.retry_count,
            }
            for item in notifications
        ]

    finally:
        db.close()


# ---------- Notification Processing ----------

from backend.notifier import process_notifications

@app.post("/notifications/process")
def process_notifications_endpoint():
    try:
        return process_notifications()

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Notification processing failed",
        )
