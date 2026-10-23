
import pandas as pd
import requests
import streamlit as st


def render_monitoring_page(api_url, api_key, incidents):
    st.markdown("## SLA & Notification Monitoring")
    st.caption(
        "Live SLA status, automated notifications and scheduler health."
    )

    headers = {"X-API-Key": api_key}

    def get_data(path):
        response = requests.get(
            f"{api_url}{path}",
            headers=headers,
            timeout=12,
        )
        response.raise_for_status()
        return response.json()

    if st.button("Refresh monitoring data"):
        st.rerun()

    try:
        scheduler = get_data("/scheduler/status")
        notifications = get_data("/notifications")
    except (requests.RequestException, ValueError) as exc:
        st.error(f"Monitoring API unavailable: {exc}")
        return

    # Calculate SLA status from incident deadlines.
    now = pd.Timestamp.now(tz="UTC")
    on_track = 0
    at_risk = 0
    breached = 0

    active_statuses = {
        "open",
        "in progress",
        "review required",
    }

    for incident in incidents:
        status = str(incident.get("status") or "").lower()

        if status not in active_statuses:
            continue

        deadline = incident.get("sla_deadline")

        if not deadline:
            continue

        try:
            deadline_time = pd.to_datetime(
                deadline, utc=True
            )

            minutes_left = (
                deadline_time - now
            ).total_seconds() / 60

            if minutes_left < 0:
                breached += 1
            elif minutes_left <= 30:
                at_risk += 1
            else:
                on_track += 1

        except (ValueError, TypeError):
            continue

    st.markdown("### SLA Overview")

    a, b, c = st.columns(3)
    a.metric("ON TRACK", on_track)
    b.metric("AT RISK", at_risk)
    c.metric("BREACHED", breached)

    st.caption(
        "Calculated from active incident deadlines. "
        "At Risk means 30 minutes or less remain."
    )

    st.divider()
    st.markdown("### Notification Monitoring")

    if isinstance(notifications, dict):
        notification_list = notifications.get(
            "notifications", []
        )
    elif isinstance(notifications, list):
        notification_list = notifications
    else:
        notification_list = []

    if not isinstance(notification_list, list):
        notification_list = []

    pending = sum(
        str(n.get("status", "")).lower() == "pending"
        for n in notification_list
    )
    simulated = sum(
        str(n.get("status", "")).lower() == "simulated"
        for n in notification_list
    )

    n1, n2, n3 = st.columns(3)
    n1.metric("TOTAL NOTIFICATIONS", len(notification_list))
    n2.metric("PENDING", pending)
    n3.metric("SIMULATED", simulated)

    st.info(
        "Notifications are simulated for this college project. "
        "No actual emails are sent."
    )

    if notification_list:
        notification_df = pd.DataFrame(notification_list)

        preferred_columns = [
            "id",
            "incident_id",
            "recipient",
            "status",
            "retry_count",
            "created_at",
        ]

        available_columns = [
            col for col in preferred_columns
            if col in notification_df.columns
        ]

        st.dataframe(
            notification_df[available_columns]
            if available_columns
            else notification_df,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No notification records found.")

    st.divider()
    st.markdown("### Automatic Scheduler")

    st.json(scheduler)
    st.caption(
        "The scheduler checks SLAs and processes pending "
        "notifications automatically every 60 seconds."
    )
