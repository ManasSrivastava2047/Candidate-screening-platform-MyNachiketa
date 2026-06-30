from flask import Blueprint, jsonify

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

    ranked, interview = apply_final_ranking(candidates)
    set_candidates(ranked)

    names = [c["name"] for c in interview]
    return jsonify({
        "message": f"Final ranking complete — {len(interview)} candidate(s) marked for interview.",
        "summary": {
            "interview": len(interview),
            "total": len(ranked),
        },
        "interview_names": names,
        "candidates": ranked,
    })
