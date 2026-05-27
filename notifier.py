from datetime import date, datetime
from notifypy import Notify
from database import KardexDB
from task_status import (
    ALERT_THRESHOLD_DAYS,
    STATUS_DUE_SOON,
    STATUS_OVERDUE,
    compute_effective_status,
    parse_deadline_date,
)


def _days_display(deadline_date: date, today: date, overdue: bool) -> str:
    days_diff = abs((deadline_date - today).days)
    unit = "day" if days_diff == 1 else "days"
    direction = "overdue by" if overdue else "due in"
    return f"{direction} {days_diff} {unit}"


def collect_deadline_alerts(
    alert_threshold_days: int = ALERT_THRESHOLD_DAYS,
    *,
    now: date | datetime | None = None,
    ) -> list[dict[str, str]]:
    db = KardexDB()
    tasks = db.get_tasks()
    today = now.date() if isinstance(now, datetime) else now or datetime.now().date()
    alerts: list[dict[str, str]] = []

    for task in tasks:
        task_id, title, status, deadline_str, _ = task
        deadline_date = parse_deadline_date(deadline_str)
        if deadline_date is None:
            continue

        effective_status = compute_effective_status(
            status,
            deadline_str,
            alert_threshold_days=alert_threshold_days,
            now=today,
        )

        if effective_status not in {STATUS_DUE_SOON, STATUS_OVERDUE}:
            continue

        alerts.append(
            {
                "task_id": str(task_id),
                "title": title,
                "deadline": deadline_date.isoformat(),
                "effective_status": effective_status,
                "time_display": _days_display(
                    deadline_date,
                    today,
                    overdue=effective_status == STATUS_OVERDUE,
                ),
            }
        )

    return alerts


def _send_deadline_notification(alert: dict[str, str]) -> None:
    alert_popup = Notify()
    status = alert["effective_status"]

    if status == STATUS_OVERDUE:
        alert_popup.title = "Kardex Overdue Task"
    else:
        alert_popup.title = "Kardex Upcoming Deadline"

    alert_popup.message = f"Task '{alert['title']}' is {alert['time_display']}."
    try:
        alert_popup.send()
    except Exception:
        return


def check_deadlines(
    alert_threshold_days: int = ALERT_THRESHOLD_DAYS,
    *,
    seen_keys: set[str] | None = None,
    now: date | datetime | None = None,
    ) -> list[dict[str, str]]:
    alerts = collect_deadline_alerts(alert_threshold_days=alert_threshold_days, now=now)
    sent_alerts: list[dict[str, str]] = []

    for alert in alerts:
        event_key = f"{alert['task_id']}:{alert['effective_status']}:{alert['deadline']}"
        if seen_keys is not None and event_key in seen_keys:
            continue

        _send_deadline_notification(alert)

        if seen_keys is not None:
            seen_keys.add(event_key)

        sent_alerts.append(alert)

    return sent_alerts