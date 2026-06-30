from flask import Blueprint, jsonify, request

from utils.store import get_jd, set_jd

jd_bp = Blueprint("jd", __name__)


@jd_bp.route("/api/save-jd", methods=["POST"])
def save_jd():
    body = request.get_json(silent=True) or {}
    jd_text = body.get("jd", "")

    if not isinstance(jd_text, str):
        return jsonify({"error": "Field 'jd' must be a string."}), 400

    jd_text = jd_text.strip()
    if not jd_text:
        return jsonify({"error": "Job description cannot be empty."}), 400

    set_jd(jd_text)

    return jsonify({
        "message": "Job description saved.",
        "length": len(jd_text),
    })


@jd_bp.route("/api/jd", methods=["GET"])
def get_job_description():
    jd = get_jd()
    return jsonify({
        "jd": jd,
        "saved": bool(jd),
        "length": len(jd),
    })
