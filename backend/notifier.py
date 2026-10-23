
import logging

from backend.database import (
    SessionLocal,
    Incident,
    Notification,
    AuditLog,
)

logger = logging.getLogger(__name__)


def process_notifications():
    """
    Process pending notification records in simulation mode.

    No external emails are sent.
    """

    db = SessionLocal()

    try:
        pending = (
            db.query(Notification)
            .filter(Notification.status == "Pending")
            .order_by(Notification.id)
            .all()
        )

        processed = []

        for notification in pending:
            incident = db.get(
                Incident,
                notification.incident_id,
            )

            if incident is None:
                notification.status = "Failed"
                notification.retry_count = (
                    notification.retry_count or 0
                ) + 1

                logger.warning(
                    "Notification %s references a missing incident",
                    notification.id,
                )
                continue

            # Simulation mode: do not send real email.
            logger.info(
                "[SIMULATED EMAIL] To=%s Incident=%s Priority=%s",
                notification.recipient,
                incident.id,
                incident.priority,
            )

            notification.status = "Simulated"

            db.add(
                AuditLog(
                    incident_id=incident.id,
                    action="NOTIFICATION_SIMULATED",
                    details=(
                        f"Notification ID: {notification.id}; "
                        f"Recipient: {notification.recipient}; "
                        f"Incident: {incident.title}; "
                        "Mode: simulation; No email sent"
                    ),
                )
            )

            processed.append({
                "notification_id": notification.id,
                "incident_id": incident.id,
                "recipient": notification.recipient,
                "status": "Simulated",
            })

        db.commit()

        return {
            "mode": "simulation",
            "processed_count": len(processed),
            "notifications": processed,
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
