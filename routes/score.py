from flask import Blueprint, jsonify

from utils.composite import rank_candidates
from utils.store import get_candidates, set_candidates

score_bp = Blueprint("score", __name__)


@score_bp.route("/api/score", methods=["POST"])
def score():
    candidates = get_candidates()
    if not candidates:
        return jsonify({"error": "No candidates loaded."}), 400

    missing = []
    if not any(c.get("jd_score") is not None for c in candidates):
        missing.append("JD evaluation")
    if not any(c.get("project_score") is not None for c in candidates):
        missing.append("project evaluation")
    if not any(c.get("github_score") is not None for c in candidates):
        missing.append("GitHub analysis")
    if not any(c.get("cgpa_score") is not None for c in candidates):
        missing.append("academic scoring")

    ranked = rank_candidates(candidates)
    set_candidates(ranked)

    top = ranked[0] if ranked else None
    return jsonify({
        "message": f"Composite scores calculated for {len(ranked)} candidate(s).",
        "warnings": missing,
        "top_candidate": top["name"] if top else None,
        "top_score": top["composite_score"] if top else None,
        "candidates": ranked,
    })
