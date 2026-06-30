from flask import Blueprint, jsonify, request

from utils.composite import rank_candidates
from utils.store import get_candidates, set_candidates
from utils.test_results import merge_test_results, parse_test_results

results_bp = Blueprint("results", __name__)


@results_bp.route("/api/upload-results", methods=["POST"])
def upload_results():
    """Extract test_la / test_code from file; apply only to shortlisted candidates."""
    candidates = get_candidates()
    if not candidates:
        return jsonify({"error": "No candidates loaded."}), 400

    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"error": "No file uploaded."}), 400

    try:
        rows, errors = parse_test_results(file.read(), file.filename)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    if not rows:
        return jsonify({
            "error": "No test scores found in file. Ensure test_la and test_code columns have values.",
            "errors": errors,
        }), 422

    outcome = merge_test_results(candidates, rows)
    merged = outcome["merged"]

    if merged == 0:
        msg = "No shortlisted candidates matched scores in the file."
        if outcome["shortlisted_total"] == 0:
            msg = "No shortlisted candidates. Run Step 8 (Shortlist) first."
        elif outcome["not_in_file"]:
            msg += f" Could not match: {', '.join(outcome['not_in_file'][:3])}"
        return jsonify({"error": msg, "summary": outcome, "errors": errors}), 400

    candidates = rank_candidates(candidates)
    set_candidates(candidates)

    return jsonify({
        "message": (
            f"Imported test scores for {merged} shortlisted candidate(s) "
            f"and updated rankings."
        ),
        "summary": {
            "merged": merged,
            "rows_in_file": len(rows),
            "shortlisted_total": outcome["shortlisted_total"],
            "skipped_not_shortlisted": outcome["skipped_not_shortlisted"],
            "not_in_file": outcome["not_in_file"],
        },
        "errors": errors,
        "candidates": candidates,
    })
