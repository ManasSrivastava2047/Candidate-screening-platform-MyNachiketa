from flask import Blueprint, jsonify

from utils.email import send_test_email, smtp_config
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
