import os
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from utils.store import get_google_account, set_google_credentials

SLOT_MINUTES = 30
DEFAULT_START_HOUR = 10


def _timezone_name(override: str | None = None) -> str:
    return (override or os.getenv("SCHEDULE_TIMEZONE", "Asia/Kolkata")).strip()


def credentials_from_store() -> Credentials:
    account = get_google_account()
    if not account:
        raise ValueError("Google account not connected. Complete Step 12 first.")

    creds_dict = account["credentials"]
    expiry = None
    if creds_dict.get("expiry"):
        expiry = datetime.fromisoformat(creds_dict["expiry"])

    creds = Credentials(
        token=creds_dict.get("token"),
        refresh_token=creds_dict.get("refresh_token"),
        token_uri=creds_dict.get("token_uri"),
        client_id=creds_dict.get("client_id"),
        client_secret=creds_dict.get("client_secret"),
        scopes=creds_dict.get("scopes"),
        expiry=expiry,
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        from utils.google_auth import credentials_to_dict

        set_google_credentials(
            credentials_to_dict(creds),
            account.get("email", ""),
        )

    return creds


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


def _extract_meet_link(event: dict) -> str:
    link = event.get("hangoutLink", "")
    if link:
        return link
    for entry in event.get("conferenceData", {}).get("entryPoints", []):
        if entry.get("entryPointType") == "video":
            return entry.get("uri", "")
    return ""


def create_interview_event(
    service,
    candidate: dict,
    start: datetime,
    tz_name: str,
) -> dict:
    end = start + timedelta(minutes=SLOT_MINUTES)
    name = candidate.get("name", "Candidate")
    email = candidate.get("email", "")

    event_body = {
        "summary": f"Visl AI Labs Interview — {name}",
        "description": (
            f"Technical interview for {name} ({email}).\n"
            "Visl AI Labs recruiting pipeline."
        ),
        "start": {"dateTime": start.isoformat(), "timeZone": tz_name},
        "end": {"dateTime": end.isoformat(), "timeZone": tz_name},
        "attendees": [{"email": email}] if email else [],
        "conferenceData": {
            "createRequest": {
                "requestId": str(uuid.uuid4()),
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        },
    }

    created = (
        service.events()
        .insert(
            calendarId="primary",
            body=event_body,
            conferenceDataVersion=1,
            sendUpdates="none",
        )
        .execute()
    )

    return {
        "event_id": created.get("id", ""),
        "meet_link": _extract_meet_link(created),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "html_link": created.get("htmlLink", ""),
    }


def schedule_interviews(
    candidates: list[dict],
    start_time: str | None = None,
    timezone: str | None = None,
) -> tuple[list[dict], list[dict], list[dict], list[str]]:
    tz_name = _timezone_name(timezone)
    interview_candidates = [c for c in candidates if c.get("status") == "interview"]
    if not interview_candidates:
        raise ValueError("No interview candidates. Run final re-score (Step 11) first.")

    creds = credentials_from_store()
    service = build("calendar", "v3", credentials=creds, cache_discovery=False)

    slot_start = parse_start_time(start_time, tz_name)
    scheduled: list[dict] = []
    log: list[dict] = []
    errors: list[str] = []

    for c in interview_candidates:
        if c.get("schedule_status") == "scheduled" and c.get("meet_link"):
            log.append({
                "name": c.get("name"),
                "email": c.get("email"),
                "status": "skipped",
                "meet_link": c.get("meet_link"),
            })
            continue

        try:
            result = create_interview_event(service, c, slot_start, tz_name)
            c["schedule_status"] = "scheduled"
            c["calendar_event_id"] = result["event_id"]
            c["meet_link"] = result["meet_link"]
            c["interview_start"] = result["start"]
            c["interview_end"] = result["end"]
            c["interview_calendar_link"] = result["html_link"]
            c.pop("schedule_error", None)
            scheduled.append(c)
            log.append({
                "name": c.get("name"),
                "email": c.get("email"),
                "status": "scheduled",
                "start": result["start"],
                "meet_link": result["meet_link"],
            })
            slot_start += timedelta(minutes=SLOT_MINUTES)
        except Exception as exc:
            c["schedule_status"] = "failed"
            c["schedule_error"] = str(exc)
            errors.append(f"{c.get('name')}: {exc}")
            log.append({
                "name": c.get("name"),
                "email": c.get("email"),
                "status": "failed",
                "error": str(exc),
            })

    return candidates, scheduled, log, errors
