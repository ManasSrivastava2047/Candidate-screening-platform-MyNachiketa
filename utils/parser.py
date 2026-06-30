import io

import pandas as pd

from utils.test_scores import normalize_email
REQUIRED = ["s_no", "name", "email", "college", "branch", "cgpa"]

OPTIONAL = ["best_ai_project", "research_work", "github", "resume"]

ALL_FIELDS = REQUIRED + OPTIONAL

ALIASES = {
    "sno": "s_no", "serial_no": "s_no", "#": "s_no",
    "bestai_project": "best_ai_project", "best_ai_pr": "best_ai_project",
    "research": "research_work", "research_w": "research_work",
    "github_profile": "github", "github_url": "github",
    "resume_link": "resume", "resume_url": "resume",
}

EMPTY_VALUES = {"", "none", "n/a", "na", "-", "null"}


def _norm_col(col: str) -> str:
    key = str(col).strip().lower().replace(" ", "_")
    return ALIASES.get(key, key)


def _val_or_na(raw: str) -> tuple[str, bool]:
    """Return (value, is_na). Empty/missing values become 'NA'."""
    cleaned = raw.strip() if raw else ""
    if cleaned.lower() in EMPTY_VALUES:
        return "NA", True
    return cleaned, False


def read_spreadsheet(file_bytes: bytes, filename: str) -> pd.DataFrame:
    name = filename.lower()
    if name.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(file_bytes), keep_default_na=False)
    elif name.endswith((".xlsx", ".xls", ".xlsm")):
        df = pd.read_excel(io.BytesIO(file_bytes), keep_default_na=False)
    else:
        raise ValueError("Unsupported file. Upload CSV, XLS, or XLSX.")
    df.columns = [_norm_col(c) for c in df.columns]
    return df.dropna(how="all")


def parse_candidates(file_bytes: bytes, filename: str) -> tuple[list[dict], list[str]]:
    df = read_spreadsheet(file_bytes, filename)
    candidates, errors = [], []

    for i, row in df.iterrows():
        data = {k: ("" if pd.isna(v) else str(v).strip()) for k, v in row.items()}
        if not any(data.values()):
            continue
        try:
            missing = [f for f in REQUIRED if not data.get(f)]
            if missing:
                raise ValueError(f"missing: {', '.join(missing)}")

            s_no = int(float(data["s_no"]))
            cgpa = float(data["cgpa"])
            if not (0 <= cgpa <= 10):
                raise ValueError("cgpa must be 0–10")
            email = normalize_email(data["email"])
            if not email or "@" not in email:
                raise ValueError("invalid email")

            na_fields: list[str] = []
            optional_vals: dict[str, str] = {}
            for field in OPTIONAL:
                value, is_na = _val_or_na(data.get(field, ""))
                optional_vals[field] = value
                if is_na:
                    na_fields.append(field)

            candidates.append({
                "s_no": s_no,
                "name": data["name"],
                "email": email,
                "college": data["college"],
                "branch": data["branch"],
                "cgpa": round(cgpa, 2),
                **optional_vals,
                "na_fields": na_fields,
                "status": "applied",
            })
        except Exception as e:
            errors.append(f"Row {int(i) + 2}: {e}")

    return candidates, errors
