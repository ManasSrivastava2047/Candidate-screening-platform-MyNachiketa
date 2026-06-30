import os

from flask import Blueprint, jsonify, redirect, request, session

from utils.google_auth import create_flow, credentials_to_dict, fetch_user_email
from utils.store import clear_google_credentials, get_google_account, set_google_credentials

auth_bp = Blueprint("auth", __name__)

if os.getenv("FLASK_ENV") != "production" and not os.getenv("RENDER"):
    os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")


@auth_bp.route("/auth/google")
def google_login():
    try:
        flow = create_flow()
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    session["oauth_state"] = state
    return redirect(auth_url)


@auth_bp.route("/auth/google/callback")
def google_callback():
    state = session.get("oauth_state")
    if not state or state != request.args.get("state"):
        return redirect("/?google=error")

    try:
        flow = create_flow()
        flow.fetch_token(authorization_response=request.url)
    except Exception:
        return redirect("/?google=error")

    creds = flow.credentials
    creds_dict = credentials_to_dict(creds)
    email = fetch_user_email(creds.token or "")
    set_google_credentials(creds_dict, email)
    session.pop("oauth_state", None)
    return redirect("/?google=connected")


@auth_bp.route("/api/google/status", methods=["GET"])
def google_status():
    account = get_google_account()
    return jsonify({
        "connected": account is not None,
        "email": account.get("email", "") if account else "",
        "redirect_uri": os.getenv(
            "GOOGLE_REDIRECT_URI",
            "http://127.0.0.1:5000/auth/google/callback",
        ),
    })


@auth_bp.route("/api/google/disconnect", methods=["POST"])
def google_disconnect():
    clear_google_credentials()
    return jsonify({"message": "Google account disconnected."})
