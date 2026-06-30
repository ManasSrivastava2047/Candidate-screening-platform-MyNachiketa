import re

EMPTY_VALUES = {"", "none", "n/a", "na", "-", "null"}

TEST_ALIASES = {
    "testla": "test_la",
    "logical_aptitude": "test_la",
    "la": "test_la",
    "test_la_score": "test_la",
    "testcode": "test_code",
    "coding": "test_code",
    "code": "test_code",
    "test_code_score": "test_code",
}


def normalize_email(raw) -> str:
    """Normalize emails for reliable matching across uploads."""
    if raw is None:
        return ""
    s = str(raw).strip().lower()
    if not s or s in EMPTY_VALUES:
        return ""
    if s.startswith("mailto:"):
        s = s[7:].strip()
    if s.startswith("<") and s.endswith(">"):
        s = s[1:-1].strip()
    s = re.sub(r"\s+", "", s)
    return s


def is_empty(raw: str) -> bool:
    return not raw or raw.strip().lower() in EMPTY_VALUES


def parse_score_value(raw, field: str) -> float:
    if raw is None or (isinstance(raw, str) and is_empty(raw)):
        raise ValueError(f"missing {field}")
    val = float(str(raw).strip().replace("%", ""))
    if not (0 <= val <= 100):
        raise ValueError(f"{field} must be 0–100")
    return round(val, 2)


def compute_test_score(test_la: float, test_code: float) -> float:
    return round((test_la * 0.4 + test_code * 0.6) / 100, 4)


def extract_test_fields(data: dict) -> dict:
    """Store test_la / test_code from upload. Scores are applied in Step 10 only."""
    la_raw = str(data.get("test_la", "")).strip()
    code_raw = str(data.get("test_code", "")).strip()
    if is_empty(la_raw) or is_empty(code_raw):
        return {}
    try:
        return {
            "test_la": parse_score_value(la_raw, "test_la"),
            "test_code": parse_score_value(code_raw, "test_code"),
        }
    except (TypeError, ValueError):
        return {}


def extract_test_scores(data: dict) -> dict:
    """Parse and fully apply test scores (used when importing a results-only file)."""
    fields = extract_test_fields(data)
    if not fields:
        return {}
    return {
        **fields,
        "test_score": compute_test_score(fields["test_la"], fields["test_code"]),
        "test_results_status": "ok",
    }


def apply_stored_test_scores(candidates: list[dict]) -> tuple[int, int, list[str]]:
    """Compute test_score from test_la/test_code saved at upload."""
    applied, missing = 0, 0
    errors: list[str] = []

    for c in candidates:
        la, code = c.get("test_la"), c.get("test_code")
        if la is None or code is None:
            missing += 1
            continue
        try:
            c["test_score"] = compute_test_score(float(la), float(code))
            c["test_results_status"] = "ok"
            applied += 1
        except (TypeError, ValueError) as exc:
            errors.append(f"{c.get('name')}: {exc}")

    return applied, missing, errors
