
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from backend.sla_monitor import check_sla
from backend.notifier import process_notifications
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(timezone="UTC")



def run_sla_monitor():
    try:
        sla_result = check_sla()

        logger.info(
            "ResolveOps SLA check: %s checked, %s breached, %s at risk",
            sla_result["total_checked"],
            sla_result["breached"],
            sla_result["at_risk"],
        )

    except Exception:
        logger.exception("ResolveOps automatic SLA check failed")
        return

    try:
        notification_result = process_notifications()

        logger.info(
            "ResolveOps notification worker: %s simulated deliveries",
            notification_result["processed_count"],
        )

    except Exception:
        logger.exception(
            "ResolveOps automatic notification processing failed"
        )

def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(
            run_sla_monitor,
            trigger="interval",
            minutes=1,
            id="resolveops_sla_monitor",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

        scheduler.start()


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
