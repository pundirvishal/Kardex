from __future__ import annotations

from datetime import date, datetime, timedelta


STATUS_IN_PROGRESS = "In Progress"
STATUS_COMPLETED = "Completed"
STATUS_ON_HOLD = "On-Hold"
STATUS_DUE_SOON = "Due Soon"
STATUS_OVERDUE = "Overdue"

ALERT_THRESHOLD_DAYS = 3

MANUAL_STATUSES = (STATUS_IN_PROGRESS, STATUS_COMPLETED, STATUS_ON_HOLD)
MANUAL_STATUS_OPTIONS = [
    (STATUS_IN_PROGRESS, STATUS_IN_PROGRESS),
    (STATUS_COMPLETED, STATUS_COMPLETED),
    (STATUS_ON_HOLD, STATUS_ON_HOLD),
]


def _coerce_now_date(now: date | datetime | None) -> date:
    if isinstance(now, datetime):
        return now.date()
    if isinstance(now, date):
        return now
    return datetime.now().date()


def parse_deadline_date(deadline_str: str | None) -> date | None:
    if not deadline_str:
        return None

    try:
        return datetime.strptime(deadline_str, "%Y-%m-%d").date()
    except ValueError:
        return None


def normalize_manual_status(status: str | None) -> str:
    normalized = (status or "").strip().lower()

    if normalized in {"completed", "done"}:
        return STATUS_COMPLETED
    if normalized in {"on-hold", "on hold", "hold"}:
        return STATUS_ON_HOLD

    return STATUS_IN_PROGRESS


def compute_effective_status(
    status: str | None,
    deadline_str: str | None,
    *,
    alert_threshold_days: int = ALERT_THRESHOLD_DAYS,
    now: date | datetime | None = None,
) -> str:
    manual_status = normalize_manual_status(status)

    if manual_status in {STATUS_COMPLETED, STATUS_ON_HOLD}:
        return manual_status

    deadline_date = parse_deadline_date(deadline_str)
    if deadline_date is None:
        return manual_status

    today = _coerce_now_date(now)

    if deadline_date < today:
        return STATUS_OVERDUE

    if deadline_date - today <= timedelta(days=alert_threshold_days):
        return STATUS_DUE_SOON

    return manual_status


def status_to_css_class(status: str) -> str:
    css_map = {
        STATUS_IN_PROGRESS: "status-in-progress",
        STATUS_COMPLETED: "status-completed",
        STATUS_ON_HOLD: "status-on-hold",
        STATUS_DUE_SOON: "status-due-soon",
        STATUS_OVERDUE: "status-overdue",
    }
    return css_map.get(status, "status-in-progress")
