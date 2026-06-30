from flask import Blueprint, jsonify

from utils.shortlist import MIN_SCORE, TOP_N, apply_shortlist
from utils.store import get_candidates, set_candidates

shortlist_bp = Blueprint("shortlist", __name__)


@shortlist_bp.route("/api/shortlist", methods=["POST"])
def shortlist():
    candidates = get_candidates()
    if not candidates:
        return jsonify({"error": "No candidates loaded."}), 400

    try:
        updated, shortlisted = apply_shortlist(candidates)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    set_candidates(updated)

    names = [c["name"] for c in shortlisted]
    return jsonify({
        "message": f"{len(shortlisted)} of {len(updated)} candidate(s) shortlisted.",
        "summary": {
            "shortlisted": len(shortlisted),
            "total": len(updated),
            "top_n": TOP_N,
            "min_score": MIN_SCORE,
        },
        "shortlisted_names": names,
        "candidates": updated,
    })
