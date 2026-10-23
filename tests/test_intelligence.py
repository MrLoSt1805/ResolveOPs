
from backend.rules import (
    determine_priority,
    assign_team,
    calculate_sla
)

from ml.classifier import classify_incident
from ml.similarity import check_duplicate


def test_network_classification():
    result = classify_incident(
        "Corporate VPN connection failed"
    )
    assert result["category"] == "Network"


def test_urgent_priority():
    assert determine_priority(
        "Urgent VPN issue before client meeting",
        "Network"
    ) == "High"


def test_security_priority():
    assert determine_priority(
        "Potential security breach reported",
        "Security"
    ) == "Critical"


def test_team_assignment():
    assert assign_team("Network") == "Network Support"


def test_sla():
    result = calculate_sla("High")
    assert result["sla_hours"] == 4


def test_exact_duplicate():
    existing = [
        {
            "id": 100,
            "description": "Corporate VPN is unavailable"
        }
    ]

    result = check_duplicate(
        "Corporate VPN is unavailable",
        existing
    )

    assert result["is_duplicate"] is True
    assert result["duplicate_of"] == 100


def test_non_duplicate():
    existing = [
        {
            "id": 100,
            "description": "Laptop keyboard is broken"
        }
    ]

    result = check_duplicate(
        "Corporate VPN is unavailable",
        existing
    )

    assert result["is_duplicate"] is False


def test_low_priority():
    assert determine_priority(
        "Monitor display is flickering",
        "Hardware"
    ) == "Low"
