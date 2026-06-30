from flask import Blueprint, jsonify

from utils.email import send_interview_email, send_test_email, smtp_config
from utils.store import get_candidates, set_candidates

emails_bp = Blueprint("emails", __name__)


@emails_bp.route("/api/send-test-emails", methods=["POST"])
def send_test_emails():
    candidates = get_candidates()
    if not candidates:
        return jsonify({"error": "No candidates loaded."}), 400

    shortlisted = [c for c in candidates if c.get("status") == "shortlisted"]
    if not shortlisted:
        return jsonify({"error": "No shortlisted candidates. Run shortlist first (Step 8)."}), 400

    try:
        cfg = smtp_config()
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    sent, failed, skipped = 0, 0, 0
    errors = []
    log = []

    for c in shortlisted:
        if c.get("test_email_status") == "sent":
            skipped += 1
            log.append({"name": c.get("name"), "email": c.get("email"), "status": "skipped"})
            continue

        try:
            send_test_email(c["email"], c["name"], cfg)
            c["test_email_status"] = "sent"
            c["status"] = "test_sent"
            c.pop("test_email_error", None)
            sent += 1
            log.append({"name": c.get("name"), "email": c.get("email"), "status": "sent"})
        except Exception as exc:
            c["test_email_status"] = "failed"
            c["test_email_error"] = str(exc)
            failed += 1
            errors.append(f"{c.get('name')}: {exc}")
            log.append({"name": c.get("name"), "email": c.get("email"), "status": "failed", "error": str(exc)})

    set_candidates(candidates)

    return jsonify({
        "message": f"Test emails — {sent} sent, {failed} failed, {skipped} skipped.",
        "summary": {"sent": sent, "failed": failed, "skipped": skipped},
        "log": log,
        "errors": errors,
        "candidates": candidates,
    })


@emails_bp.route("/api/send-interview-emails", methods=["POST"])
def send_interview_emails():
    candidates = get_candidates()
    if not candidates:
        return jsonify({"error": "No candidates loaded."}), 400

    interview = [c for c in candidates if c.get("status") == "interview"]
    if not interview:
        return jsonify({"error": "No interview candidates. Run final re-score (Step 11) first."}), 400

    try:
        cfg = smtp_config()
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    sent, failed, skipped, not_scheduled = 0, 0, 0, 0
    errors = []
    log = []

    for c in interview:
        if c.get("interview_email_status") == "sent":
            skipped += 1
            log.append({"name": c.get("name"), "email": c.get("email"), "status": "skipped"})
            continue

        if c.get("schedule_status") != "scheduled" or not c.get("meet_link") or not c.get("interview_start"):
            not_scheduled += 1
            log.append({
                "name": c.get("name"),
                "email": c.get("email"),
                "status": "not_scheduled",
            })
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

    set_candidates(candidates)

    return jsonify({
        "message": (
            f"Interview emails — {sent} sent, {failed} failed, "
            f"{skipped} skipped, {not_scheduled} not scheduled."
        ),
        "summary": {
            "sent": sent,
            "failed": failed,
            "skipped": skipped,
            "not_scheduled": not_scheduled,
        },
        "log": log,
        "errors": errors,
        "candidates": candidates,
    })
