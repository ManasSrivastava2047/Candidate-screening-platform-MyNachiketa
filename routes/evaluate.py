from flask import Blueprint, jsonify

from utils.evaluate import evaluate_candidate
from utils.store import get_candidates, get_jd, set_candidates

evaluate_bp = Blueprint("evaluate", __name__)


@evaluate_bp.route("/api/evaluate", methods=["POST"])
def evaluate():
    candidates = get_candidates()
    if not candidates:
        return jsonify({"error": "No candidates loaded. Upload a spreadsheet first."}), 400

    jd = get_jd()
    if not jd:
        return jsonify({"error": "No job description saved. Save a JD first."}), 400

    ok, failed = 0, 0
    errors = []

    for c in candidates:
        try:
            scores = evaluate_candidate(jd, c)
            c["jd_score"] = scores["jd_score"]
            c["jd_reasoning"] = scores["jd_reasoning"]
            c["project_score"] = scores["project_score"]
            c["project_reasoning"] = scores["project_reasoning"]
            c["eval_status"] = "ok"
            c["status"] = "evaluated"
            ok += 1
        except Exception as exc:
            c["eval_status"] = "failed"
            c["eval_error"] = str(exc)
            errors.append(f"{c.get('name', '?')}: {exc}")
            failed += 1

    set_candidates(candidates)

    return jsonify({
        "message": f"Evaluated {ok} candidate(s)." + (f" {failed} failed." if failed else ""),
        "summary": {"ok": ok, "failed": failed},
        "errors": errors,
        "candidates": candidates,
    })
