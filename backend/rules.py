
from datetime import datetime, timedelta, timezone

TEAM_MAPPING = {
    "Network": "Network Support",
    "Hardware": "Hardware Support",
    "Software": "Application Support",
    "Access": "Identity and Access Management",
    "Security": "Security Operations"
}

SLA_HOURS = {
    "Critical": 1,
    "High": 4,
    "Medium": 8,
    "Low": 24
}

CRITICAL_KEYWORDS = [
    "security breach",
    "data leak",
    "ransomware",
    "data stolen",
    "confidential data exposed",
    "company data leaked",
    "critical outage"
]

HIGH_KEYWORDS = [
    "urgent",
    "immediately",
    "client meeting",
    "production down",
    "business stopped",
    "cannot work",
    "as soon as possible"
]


def determine_priority(text, category):
    text = text.lower()

    if any(word in text for word in CRITICAL_KEYWORDS):
        return "Critical"

    if category == "Security":
        return "High"

    if any(word in text for word in HIGH_KEYWORDS):
        return "High"

    if category in ["Network", "Access"]:
        return "Medium"

    return "Low"


def assign_team(category):
    return TEAM_MAPPING.get(
        category,
        "IT Service Desk"
    )


def calculate_sla(priority):
    hours = SLA_HOURS.get(priority, 24)

    deadline = (
        datetime.now(timezone.utc)
        + timedelta(hours=hours)
    )

    return {
        "sla_hours": hours,
        "sla_deadline": deadline.replace(
            tzinfo=None
        )
    }
