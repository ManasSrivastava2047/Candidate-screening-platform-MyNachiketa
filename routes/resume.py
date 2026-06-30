from flask import Blueprint, jsonify

from utils.resume import process_candidate_resume
from utils.store import get_candidates, set_candidates

resume_bp = Blueprint("resume", __name__)


@resume_bp.route("/api/process-resumes", methods=["POST"])
def process_resumes():
    candidates = get_candidates()
    if not candidates:
        return jsonify({"error": "No candidates loaded. Upload a spreadsheet first."}), 400

    ok, failed, skipped = 0, 0, 0
    for c in candidates:
        process_candidate_resume(c)
        status = c.get("resume_status")
        if status == "ok":
            ok += 1
        elif status == "na":
            skipped += 1
        else:
            failed += 1

    set_candidates(candidates)

    return jsonify({
        "message": f"Processed {len(candidates)} resume(s).",
        "summary": {"ok": ok, "failed": failed, "skipped": skipped},
        "candidates": candidates,
    })
