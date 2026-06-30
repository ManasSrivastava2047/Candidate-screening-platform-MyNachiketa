from utils.email import send_interview_email, smtp_config


def send_interview_invites(candidates: list[dict]) -> dict:
    """Send interview emails to candidates with assigned slots."""
    interview = [c for c in candidates if c.get("status") == "interview"]
    if not interview:
        return {
            "sent": 0,
            "failed": 0,
            "skipped": 0,
            "not_ready": 0,
            "errors": [],
            "log": [],
        }

    cfg = smtp_config()
    sent, failed, skipped, not_ready = 0, 0, 0, 0
    errors: list[str] = []
    log: list[dict] = []

    for c in interview:
        if c.get("interview_email_status") == "sent":
            skipped += 1
            log.append({"name": c.get("name"), "email": c.get("email"), "status": "skipped"})
            continue

        if not c.get("meet_link") or not c.get("interview_start"):
            not_ready += 1
            log.append({"name": c.get("name"), "email": c.get("email"), "status": "not_ready"})
            continue

        try:
            send_interview_email(
                c["email"],
                c["name"],
                c["interview_start"],
                c["meet_link"],
                cfg,
            )
            c["interview_email_status"] = "sent"
            c.pop("interview_email_error", None)
            sent += 1
            log.append({"name": c.get("name"), "email": c.get("email"), "status": "sent"})
        except Exception as exc:
            c["interview_email_status"] = "failed"
            c["interview_email_error"] = str(exc)
            failed += 1
            errors.append(f"{c.get('name')}: {exc}")
            log.append({
                "name": c.get("name"),
                "email": c.get("email"),
                "status": "failed",
                "error": str(exc),
            })

    return {
        "sent": sent,
        "failed": failed,
        "skipped": skipped,
        "not_ready": not_ready,
        "errors": errors,
        "log": log,
    }
