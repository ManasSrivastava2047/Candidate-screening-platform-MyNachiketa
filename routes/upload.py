from flask import Blueprint, jsonify, request

from utils.parser import parse_candidates
from utils.store import clear_candidates, get_candidates, set_candidates

upload_bp = Blueprint("upload", __name__)


@upload_bp.route("/api/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"error": "No file uploaded."}), 400

    data, errors = parse_candidates(file.read(), file.filename)
    if not data:
        return jsonify({"error": "No valid rows found.", "errors": errors}), 422

    set_candidates(data)

    return jsonify({
        "message": f"Loaded {len(data)} candidate(s).",
        "count": len(data),
        "candidates": data,
        "errors": errors,
    })


@upload_bp.route("/api/candidates", methods=["GET"])
def list_candidates():
    candidates = get_candidates()
    return jsonify({"candidates": candidates, "count": len(candidates)})


@upload_bp.route("/api/candidates", methods=["DELETE"])
def clear():
    clear_candidates()
    return jsonify({"message": "Candidates cleared."})
