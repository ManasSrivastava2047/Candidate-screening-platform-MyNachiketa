import pandas as pd

from utils.parser import read_spreadsheet
from utils.test_scores import (
    TEST_ALIASES,
    compute_test_score,
    extract_test_fields,
    is_empty,
    normalize_email,
)

# Shortlisted pipeline — includes test_sent (after invitation emails)
SHORTLIST_STATUSES = frozenset({"shortlisted", "test_sent"})


def _norm_result_col(col: str) -> str:
    key = str(col).strip().lower().replace(" ", "_")
    return TEST_ALIASES.get(key, key)


def _cell_str(val) -> str:
    if pd.isna(val):
        return ""
    if isinstance(val, float) and val == int(val):
        return str(int(val))
    return str(val).strip()


def parse_test_results(file_bytes: bytes, filename: str) -> tuple[list[dict], list[str]]:
    """
    Extract test_la / test_code from a results file OR full candidate spreadsheet.
    Extra columns are ignored. Rows without both scores are skipped.
    """
    df = read_spreadsheet(file_bytes, filename)
    df.columns = [_norm_result_col(c) for c in df.columns]

    if "email" not in df.columns:
        raise ValueError("Missing column: email")

    if "test_la" not in df.columns or "test_code" not in df.columns:
        raise ValueError(
            "Missing test score columns. Expected test_la and test_code "
            "(aliases: logical_aptitude, coding, etc.)."
        )

    results, errors, skipped = [], [], 0

    for i, row in df.iterrows():
        data = {k: _cell_str(v) for k, v in row.items()}
        if not any(data.values()):
            continue

        email = normalize_email(data.get("email", ""))
        if not email:
            continue
        if "@" not in email:
            errors.append(f"Row {int(i) + 2}: invalid email")
            continue

        fields = extract_test_fields(data)
        if not fields:
            skipped += 1
            continue

        results.append({
            "email": email,
            **fields,
            "test_score": compute_test_score(fields["test_la"], fields["test_code"]),
        })

    if not results and skipped:
        errors.append(f"{skipped} row(s) had no test_la/test_code values to import.")

    return results, errors


def merge_test_results(candidates: list[dict], results: list[dict]) -> dict:
    """
    Apply file scores only to shortlisted / test_sent candidates, matched by email.
    """
    scores_by_email: dict[str, dict] = {}
    for r in results:
        email = normalize_email(r.get("email", ""))
        if email:
            scores_by_email[email] = r

    merged = 0
    skipped_not_shortlisted = 0
    not_in_file: list[str] = []

    for cand in candidates:
        status = cand.get("status", "applied")
        email = normalize_email(cand.get("email", ""))

        if status not in SHORTLIST_STATUSES:
            if email in scores_by_email:
                skipped_not_shortlisted += 1
            continue

        row = scores_by_email.get(email)
        if not row:
            not_in_file.append(cand.get("name") or email)
            continue

        cand.update({
            "test_la": row["test_la"],
            "test_code": row["test_code"],
            "test_score": row["test_score"],
            "test_results_status": "ok",
        })
        merged += 1

    return {
        "merged": merged,
        "skipped_not_shortlisted": skipped_not_shortlisted,
        "not_in_file": not_in_file,
        "shortlisted_total": sum(1 for c in candidates if c.get("status") in SHORTLIST_STATUSES),
    }
