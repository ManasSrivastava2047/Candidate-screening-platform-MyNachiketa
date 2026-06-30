from flask import Blueprint, jsonify

from utils.github_eval import analyze_candidate_github
from utils.store import get_candidates, get_jd, set_candidates

github_bp = Blueprint("github", __name__)


@github_bp.route("/api/github", methods=["POST"])
def analyze_github():
    candidates = get_candidates()
    if not candidates:
        return jsonify({"error": "No candidates loaded."}), 400

    jd = get_jd()
    if not jd:
        return jsonify({"error": "Save a job description first."}), 400

    ok, failed, skipped = 0, 0, 0
    errors = []

    for c in candidates:
        result = analyze_candidate_github(jd, c)
        c.update(result)
        status = result.get("github_status")
        if status == "ok":
            ok += 1
        elif status == "na":
            skipped += 1
        else:
            failed += 1
            errors.append(f"{c.get('name')}: {result.get('github_error', 'failed')}")

    set_candidates(candidates)

    return jsonify({
        "message": f"GitHub analysis complete for {len(candidates)} candidate(s).",
        "summary": {"ok": ok, "failed": failed, "skipped": skipped},
        "errors": errors,
        "candidates": candidates,
    })
