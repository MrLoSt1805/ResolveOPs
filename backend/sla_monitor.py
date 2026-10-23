
from datetime import datetime, timedelta, timezone

from backend.database import SessionLocal, Incident, AuditLog, Notification


def check_sla():
    """
    Check active incidents for SLA warnings and breaches.

    Creates audit events once per incident per event type.
    Returns a summary for the API/dashboard.
    """

    db = SessionLocal()

    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        incidents = (
            db.query(Incident)
            .filter(
                Incident.status.in_([
                    "Open",
                    "In Progress",
                    "Review Required",
                ]),
                Incident.sla_deadline.isnot(None),
            )
            .all()
        )

        results = []

        for incident in incidents:
            deadline = incident.sla_deadline

            if deadline <= now:
                sla_status = "Breached"
                action = "SLA_ESCALATED"

            elif deadline <= now + timedelta(minutes=30):
                sla_status = "At Risk"
                action = "SLA_WARNING"

            else:
                sla_status = "On Track"
                action = None

            if action is not None:
                existing_log = (
                    db.query(AuditLog)
                    .filter(
                        AuditLog.incident_id == incident.id,
                        AuditLog.action == action,
                    )
                    .first()
                )

                if existing_log is None:
                    db.add(
                        AuditLog(
                            incident_id=incident.id,
                            action=action,
                            details=(
                                f"SLA status: {sla_status}; "
                                f"Priority: {incident.priority}; "
                                f"Deadline (UTC): {deadline.isoformat()}; "
                                f"Checked (UTC): {now.isoformat()}"
                            ),
                        )
                    )
            
            # Create a notification for any breached incident
            # that does not already have a notification.
            if sla_status == "Breached":
                existing_notification = (
                    db.query(Notification)
                    .filter(
                        Notification.incident_id == incident.id,
                    )
                    .first()
                )

                if existing_notification is None:
                    db.add(
                        Notification(
                            incident_id=incident.id,
                            recipient=incident.email,
                            status="Pending",
                            retry_count=0,
                        )
                    )
        

            results.append({
                "incident_id": incident.id,
                "title": incident.title,
                "priority": incident.priority,
                "assigned_team": incident.assigned_team,
                "status": incident.status,
                "sla_deadline": deadline.isoformat(),
                "sla_status": sla_status,
            })

        db.commit()

        return {
            "checked_at": now.isoformat(),
            "total_checked": len(results),
            "on_track": sum(
                i["sla_status"] == "On Track" for i in results
            ),
            "at_risk": sum(
                i["sla_status"] == "At Risk" for i in results
            ),
            "breached": sum(
                i["sla_status"] == "Breached" for i in results
            ),
            "incidents": results,
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
