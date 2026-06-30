WEIGHTS = {
    "jd_score": 0.30,
    "github_score": 0.25,
    "test_score": 0.25,
    "cgpa_score": 0.10,
    "project_score": 0.10,
}


def _safe_score(candidate: dict, key: str) -> float:
    val = candidate.get(key)
    if val is None:
        return 0.0
    try:
        return max(0.0, min(1.0, float(val)))
    except (TypeError, ValueError):
        return 0.0


def compute_composite(candidate: dict) -> float:
    total = sum(_safe_score(candidate, key) * weight for key, weight in WEIGHTS.items())
    return round(total, 4)


def composite_breakdown(candidate: dict) -> str:
    parts = []
    for key, weight in WEIGHTS.items():
        score = _safe_score(candidate, key)
        label = key.replace("_score", "").upper()
        if key == "cgpa_score":
            label = "CGPA"
        parts.append(f"{label} {score:.2f} x {weight:.0%}")
    return " + ".join(parts)


def rank_candidates(candidates: list[dict]) -> list[dict]:
    for c in candidates:
        c["composite_score"] = compute_composite(c)
        c["composite_breakdown"] = composite_breakdown(c)
        c["score_status"] = "ok"

    ranked = sorted(
        candidates,
        key=lambda c: (-c["composite_score"], c.get("s_no", 0)),
    )
    for i, c in enumerate(ranked, start=1):
        c["rank"] = i

    return ranked
