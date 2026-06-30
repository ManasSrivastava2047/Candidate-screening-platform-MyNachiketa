"""Single frontend bundle — no script load-order issues."""
from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.route("/api/health")
def health():
    return jsonify({"status": "ok", "message": "Server is running"})
