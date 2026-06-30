import json
import os
import uuid
from pathlib import Path

from flask import g, session

_STORE_CACHE_KEY = "visl_store"


def _store_dir() -> Path:
    custom = os.getenv("STORE_DIR", "").strip()
    if custom:
        return Path(custom)
    if os.getenv("RENDER"):
        return Path("/tmp/visl-recruit-stores")
    return Path(__file__).resolve().parent.parent / "data" / "stores"


def _store_path(sid: str) -> Path:
    safe = "".join(c for c in sid if c.isalnum() or c == "-")
    return _store_dir() / f"{safe}.json"


def _default_store() -> dict:
    return {
        "candidates": [],
        "job_description": "",
        "google_credentials": None,
        "google_email": "",
    }


def _ensure_sid() -> str:
    if "sid" not in session:
        session["sid"] = str(uuid.uuid4())
        session.modified = True
    return session["sid"]


def _load(sid: str) -> dict:
    path = _store_path(sid)
    if not path.exists():
        return _default_store()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {**_default_store(), **data}
    except (OSError, json.JSONDecodeError):
        pass
    return _default_store()


def _persist(store: dict) -> None:
    sid = _ensure_sid()
    directory = _store_dir()
    directory.mkdir(parents=True, exist_ok=True)
    _store_path(sid).write_text(json.dumps(store), encoding="utf-8")


def get_store() -> dict:
    if getattr(g, _STORE_CACHE_KEY, None) is None:
        setattr(g, _STORE_CACHE_KEY, _load(_ensure_sid()))
    return getattr(g, _STORE_CACHE_KEY)


def get_candidates() -> list[dict]:
    return get_store()["candidates"]


def set_candidates(data: list[dict]) -> None:
    store = get_store()
    store["candidates"] = data
    _persist(store)


def clear_candidates() -> None:
    store = get_store()
    store["candidates"] = []
    _persist(store)


def get_jd() -> str:
    return get_store()["job_description"]


def set_jd(text: str) -> None:
    store = get_store()
    store["job_description"] = text
    _persist(store)


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
    _persist(store)


def clear_google_credentials() -> None:
    store = get_store()
    store["google_credentials"] = None
    store["google_email"] = ""
    _persist(store)
