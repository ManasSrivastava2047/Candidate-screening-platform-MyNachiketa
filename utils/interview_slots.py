import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

SLOT_MINUTES = 30
DEFAULT_START_HOUR = 10


def _timezone_name() -> str:
    return os.getenv("SCHEDULE_TIMEZONE", "Asia/Kolkata").strip()


def meet_link() -> str:
    link = os.getenv("INTERVIEW_MEET_LINK", "").strip()
    if not link:
        raise ValueError("INTERVIEW_MEET_LINK must be set in .env (your Google Meet room URL).")
    return link


def default_start_time(tz_name: str) -> datetime:
    tz = ZoneInfo(tz_name)
    now = datetime.now(tz)
    start = now.replace(hour=DEFAULT_START_HOUR, minute=0, second=0, microsecond=0)
    if start <= now:
        start += timedelta(days=1)
    while start.weekday() >= 5:
        start += timedelta(days=1)
    return start


def parse_start_time(value: str | None, tz_name: str) -> datetime:
    tz = ZoneInfo(tz_name)
    if not value:
        return default_start_time(tz_name)

    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"

    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz)
    else:
        dt = dt.astimezone(tz)
    return dt


def assign_interview_slots(
    candidates: list[dict],
    start_time: str | None = None,
) -> tuple[list[dict], list[dict]]:
    """Assign 30-min sequential slots and Meet link to interview candidates."""
    tz_name = _timezone_name()
    link = meet_link()
    interview_candidates = [c for c in candidates if c.get("status") == "interview"]
    if not interview_candidates:
        return candidates, []

    slot_start = parse_start_time(start_time, tz_name)
    scheduled: list[dict] = []

    for c in interview_candidates:
        end = slot_start + timedelta(minutes=SLOT_MINUTES)
        c["schedule_status"] = "scheduled"
        c["meet_link"] = link
        c["interview_start"] = slot_start.isoformat()
        c["interview_end"] = end.isoformat()
        c.pop("schedule_error", None)
        scheduled.append(c)
        slot_start = end

    return candidates, scheduled
