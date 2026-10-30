"""Calendar-day durations, independent of daylight-saving transitions."""
from datetime import date, datetime, time, timedelta
from fastapi import HTTPException

MAX_DURATION_DAYS = 3650


def event_duration_days(start: str | None, end: str | None) -> int:
    if not start or not end:
        return 1
    try:
        return max(1, (date.fromisoformat(end[:10]) - date.fromisoformat(start[:10])).days + 1)
    except ValueError:
        return 1


def end_date_for_duration(start: str | None, days: int) -> str | None:
    if not start:
        if days != 1:
            raise HTTPException(status_code=422, detail="Choose a start date before setting duration")
        return None
    try:
        last_day = date.fromisoformat(start[:10]) + timedelta(days=days - 1)
        return datetime.combine(last_day, time(23, 59, 59), tzinfo=datetime.fromisoformat(start).tzinfo).isoformat()
    except (ValueError, OverflowError):
        raise HTTPException(status_code=422, detail="Invalid event date") from None


def validate_future_instant(value: str | None) -> None:
    """Validate offset-aware timestamps; legacy local dates have no reliable timezone."""
    if not value:
        return
    try:
        start = datetime.fromisoformat(value)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid event date") from None
    if start.tzinfo is not None and start < datetime.now(start.tzinfo).replace(second=0, microsecond=0):
        raise HTTPException(status_code=422, detail="Event time must not be in the past")
