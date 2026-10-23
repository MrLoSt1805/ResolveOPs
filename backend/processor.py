
from backend.database import (
    SessionLocal,
    Incident,
    AuditLog
)

from backend.rules import (
    determine_priority,
    assign_team,
    calculate_sla
)

from ml.classifier import classify_incident
from ml.similarity import check_duplicate


def process_incident(incident_id):
    db = SessionLocal()

    try:
        incident = db.get(Incident, incident_id)

        if incident is None:
            raise ValueError("Incident not found")

        if incident.status != "Pending":
            raise ValueError(
                "Only Pending incidents can be processed"
            )

        text = (
            incident.title + ". "
            + incident.description
        )

        # Step 1: NLP classification
        result = classify_incident(text)

        category = result["category"]
        confidence = result["confidence"]

        # Step 2: Priority determination
        priority = determine_priority(
            text,
            category
        )

        # Step 3: Duplicate detection
        existing = db.query(Incident).filter(
            Incident.id != incident.id,
            Incident.status.in_([
                "Pending",
                "Open",
                "In Progress",
                "Review Required"
            ])
        ).all()

        existing_data = [
            {
                "id": item.id,
                "description": (
                    item.title + ". " + item.description
                )
            }
            for item in existing
        ]

        duplicate = check_duplicate(
            text,
            existing_data
        )

        # Step 4: Team assignment
        team = assign_team(category)

        # Step 5: SLA
        sla = calculate_sla(priority)

        # Step 6: Update incident
        incident.category = category
        incident.priority = priority
        incident.assigned_team = team
        incident.confidence = str(confidence)
        incident.duplicate_of = duplicate["duplicate_of"]
        incident.sla_deadline = sla["sla_deadline"]

        if duplicate["is_duplicate"]:
            incident.status = "Review Required"
        elif confidence < 0.35:
            incident.status = "Review Required"
        else:
            incident.status = "Open"

        # Step 7: Audit log
        actions = [
            (
                "NLP_CLASSIFIED",
                f"Category={category}; Confidence={confidence}"
            ),
            (
                "PRIORITY_ASSIGNED",
                f"Priority={priority}"
            ),
            (
                "DUPLICATE_CHECKED",
                str(duplicate)
            ),
            (
                "TEAM_ASSIGNED",
                f"Team={team}"
            ),
            (
                "SLA_CALCULATED",
                f"Deadline={sla['sla_deadline']}"
            ),
            (
                "PROCESSING_COMPLETED",
                f"Status={incident.status}"
            )
        ]

        for action, details in actions:
            db.add(AuditLog(
                incident_id=incident.id,
                action=action,
                details=details
            ))

        db.commit()
        db.refresh(incident)

        return {
            "incident_id": incident.id,
            "category": category,
            "confidence": confidence,
            "priority": priority,
            "assigned_team": team,
            "duplicate": duplicate,
            "sla_hours": sla["sla_hours"],
            "sla_deadline": str(sla["sla_deadline"]),
            "status": incident.status
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
