from flask import Blueprint, jsonify

from utils.academic import score_candidate_academic
from utils.store import get_candidates, get_jd, set_candidates

academic_bp = Blueprint("academic", __name__)


@academic_bp.route("/api/academic-score", methods=["POST"])
def academic_score():
    candidates = get_candidates()
    if not candidates:
        return jsonify({"error": "No candidates loaded."}), 400

    jd = get_jd() or ""

    ok, failed = 0, 0
    errors = []

    for c in candidates:
        result = score_candidate_academic(jd, c)
        c.update(result)
        if result.get("academic_status") == "ok":
            ok += 1
        else:
            failed += 1
            errors.append(f"{c.get('name')}: {result.get('academic_error', 'failed')}")

    set_candidates(candidates)

    return jsonify({
        "message": f"Academic scoring complete for {len(candidates)} candidate(s).",
        "summary": {"ok": ok, "failed": failed},
        "errors": errors,
        "candidates": candidates,
    })
