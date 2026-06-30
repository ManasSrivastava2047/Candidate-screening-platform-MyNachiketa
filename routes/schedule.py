from flask import Blueprint, jsonify, request

from utils.schedule import schedule_interviews
from utils.store import get_candidates, set_candidates

schedule_bp = Blueprint("schedule", __name__)


@schedule_bp.route("/api/schedule", methods=["POST"])
def schedule():
    candidates = get_candidates()
    if not candidates:
        return jsonify({"error": "No candidates loaded."}), 400

    body = request.get_json(silent=True) or {}
    start_time = body.get("start_time")
    timezone = body.get("timezone")

    try:
        updated, scheduled, log, errors = schedule_interviews(
            candidates,
            start_time=start_time,
            timezone=timezone,
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": f"Scheduling failed: {exc}"}), 500

    set_candidates(updated)

    skipped = sum(1 for e in log if e.get("status") == "skipped")
    failed = sum(1 for e in log if e.get("status") == "failed")

    return jsonify({
        "message": (
            f"Interview scheduling — {len(scheduled)} scheduled, "
            f"{failed} failed, {skipped} skipped."
        ),
        "summary": {
            "scheduled": len(scheduled),
            "failed": failed,
            "skipped": skipped,
        },
        "log": log,
        "errors": errors,
        "candidates": updated,
    })
