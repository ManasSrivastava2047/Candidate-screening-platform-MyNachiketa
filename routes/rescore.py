from flask import Blueprint, jsonify, request

from utils.interview_emails import send_interview_invites
from utils.interview_slots import assign_interview_slots
from utils.rescore import apply_final_ranking
from utils.store import get_candidates, set_candidates

rescore_bp = Blueprint("rescore", __name__)


@rescore_bp.route("/api/rescore", methods=["POST"])
def rescore():
    candidates = get_candidates()
    if not candidates:
        return jsonify({"error": "No candidates loaded."}), 400

    if not any(c.get("test_results_status") == "ok" for c in candidates):
        return jsonify({"error": "No test scores found. Upload test results in Step 10 first."}), 400

    body = request.get_json(silent=True) or {}
    start_time = body.get("start_time")

    ranked, interview = apply_final_ranking(candidates)

    try:
        ranked, scheduled = assign_interview_slots(ranked, start_time=start_time)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    email_summary = {"sent": 0, "failed": 0, "skipped": 0, "errors": []}
    if scheduled:
        try:
            email_summary = send_interview_invites(ranked)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

    set_candidates(ranked)

    names = [c["name"] for c in interview]
    msg = f"Final ranking complete — {len(interview)} candidate(s) marked for interview."
    if scheduled:
        msg += f" {len(scheduled)} slot(s) assigned."
    if email_summary["sent"]:
        msg += f" {email_summary['sent']} interview email(s) sent."
    if email_summary["failed"]:
        msg += f" {email_summary['failed']} email(s) failed."

    return jsonify({
        "message": msg,
        "summary": {
            "interview": len(interview),
            "scheduled": len(scheduled),
            "emails_sent": email_summary["sent"],
            "emails_failed": email_summary["failed"],
            "emails_skipped": email_summary["skipped"],
            "total": len(ranked),
        },
        "interview_names": names,
        "email_log": email_summary.get("log", []),
        "errors": email_summary.get("errors", []),
        "candidates": ranked,
    })
