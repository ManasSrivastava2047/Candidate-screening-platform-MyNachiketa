import os

import requests
from google_auth_oauthlib.flow import Flow

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
]


def redirect_uri() -> str:
    return os.getenv("GOOGLE_REDIRECT_URI", "http://127.0.0.1:5000/auth/google/callback")


def _client_config() -> dict:
    client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        raise ValueError("GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set in .env")
    return {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri()],
        }
    }


def create_flow() -> Flow:
    return Flow.from_client_config(
        _client_config(),
        scopes=SCOPES,
        redirect_uri=redirect_uri(),
    )


def credentials_to_dict(credentials) -> dict:
    return {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": list(credentials.scopes or []),
        "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
    }


def fetch_user_email(access_token: str) -> str:
    try:
        r = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=15,
        )
        if r.status_code == 200:
            return r.json().get("email", "")
    except requests.RequestException:
        pass
    return ""
