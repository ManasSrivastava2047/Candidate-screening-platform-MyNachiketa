import uuid
from flask import session

_stores: dict[str, dict] = {}


def _default_store() -> dict:
    return {
        "candidates": [],
        "job_description": "",
        "google_credentials": None,
        "google_email": "",
    }


def get_store() -> dict:
    if "sid" not in session:
        session["sid"] = str(uuid.uuid4())
    sid = session["sid"]
    if sid not in _stores:
        _stores[sid] = _default_store()
    return _stores[sid]


def get_candidates() -> list[dict]:
    return get_store()["candidates"]


def set_candidates(data: list[dict]) -> None:
    get_store()["candidates"] = data


def clear_candidates() -> None:
    get_store()["candidates"] = []


def get_jd() -> str:
    return get_store()["job_description"]


def set_jd(text: str) -> None:
    get_store()["job_description"] = text


def get_google_account() -> dict | None:
    store = get_store()
    creds = store.get("google_credentials")
    if not creds:
        return None
    return {"credentials": creds, "email": store.get("google_email", "")}


def set_google_credentials(creds: dict, email: str = "") -> None:
    store = get_store()
    store["google_credentials"] = creds
    store["google_email"] = email


def clear_google_credentials() -> None:
    store = get_store()
    store["google_credentials"] = None
    store["google_email"] = ""
