
import os
from pathlib import Path

import requests
import streamlit as st
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

API_URL = os.getenv(
    "RESOLVEOPS_API_URL",
    "http://127.0.0.1:8000",
).rstrip("/")

API_KEY = os.getenv("RESOLVEOPS_API_KEY", "")

HEADERS = {
    "X-API-Key": API_KEY,
    "Accept": "application/json",
}


def api_get(path):
    response = requests.get(
        f"{API_URL}{path}",
        headers=HEADERS,
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


def api_post(path, payload):
    response = requests.post(
        f"{API_URL}{path}",
        headers=HEADERS,
        json=payload,
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


def render_review_page():
    st.title("Human Review Center")
    st.caption(
        "Review low-confidence AI classifications, "
        "approve assignments, and maintain an audit trail."
    )

    if not API_KEY:
        st.error("API key is missing from the .env file.")
        return

    if st.button("Refresh Review Queue", key="refresh_reviews"):
        st.rerun()

    try:
        incidents = api_get("/incidents/review")
    except requests.RequestException as exc:
        st.error(f"Could not load review queue: {exc}")
        return

    st.metric("Awaiting Human Review", len(incidents))

    if not incidents:
        st.success("All incidents have been reviewed.")
        return

    incident_options = {
        f"#{i['id']} — {i['title']}": i
        for i in incidents
    }

    selected_label = st.selectbox(
        "Select incident to review",
        list(incident_options.keys()),
    )

    incident = incident_options[selected_label]

    st.divider()

    st.subheader(f"Incident #{incident['id']}")
    st.write("**Title:**", incident["title"])
    st.write("**Description:**", incident["description"])

    st.subheader("AI Recommendation")

    col1, col2, col3 = st.columns(3)

    col1.info(f"Category: {incident.get('category') or 'Unknown'}")
    col2.info(f"Priority: {incident.get('priority') or 'Unknown'}")
    col3.info(
        f"Assigned Team: {incident.get('assigned_team') or 'Unknown'}"
    )

    st.divider()

    reviewer = st.text_input(
        "Reviewer name",
        placeholder="Enter your name",
    )

    decision = st.radio(
        "Review decision",
        ["Approve AI recommendation", "Override AI recommendation"],
    )

    category = incident.get("category") or ""
    priority = incident.get("priority") or "Medium"
    assigned_team = incident.get("assigned_team") or ""

    if decision == "Override AI recommendation":
        st.subheader("Correct AI Decision")

        category = st.selectbox(
            "Correct category",
            ["Network", "Hardware", "Software", "Security", "Access"],
        )

        priority = st.selectbox(
            "Correct priority",
            ["Low", "Medium", "High", "Critical"],
        )

        assigned_team = st.text_input(
            "Correct assigned team",
            value=assigned_team,
        )

    notes = st.text_area(
        "Review notes",
        placeholder="Explain the approval or correction...",
    )

    if st.button(
        "Submit Review Decision",
        type="primary",
        use_container_width=True,
    ):
        if len(reviewer.strip()) < 2:
            st.error("Enter a reviewer name with at least 2 characters.")
            return

        payload = {
            "reviewer": reviewer.strip(),
            "decision": (
                "approve"
                if decision == "Approve AI recommendation"
                else "override"
            ),
            "category": category,
            "priority": priority,
            "assigned_team": assigned_team,
            "notes": notes,
        }

        try:
            result = api_post(
                f"/incidents/{incident['id']}/review",
                payload,
            )

            st.success(
                f"Incident #{result['incident_id']} reviewed successfully. "
                f"New status: {result['status']}"
            )

            st.info(
                "The review decision has been saved to SQLite "
                "and recorded in the audit trail."
            )

        except requests.HTTPError as exc:
            detail = ""
            if exc.response is not None:
                try:
                    detail = exc.response.json().get("detail", "")
                except ValueError:
                    detail = exc.response.text
            st.error(f"Review failed: {detail or str(exc)}")

        except requests.RequestException as exc:
            st.error(f"Connection error: {exc}")
