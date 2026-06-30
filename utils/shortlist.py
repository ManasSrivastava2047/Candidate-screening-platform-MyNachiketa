TOP_N = 5
MIN_SCORE = 0.6


def apply_shortlist(candidates: list[dict], top_n: int = TOP_N, min_score: float = MIN_SCORE) -> tuple[list[dict], list[dict]]:
    if not candidates:
        return candidates, []

    if not any(c.get("composite_score") is not None for c in candidates):
        raise ValueError("Run composite scoring first (Step 7).")

    shortlisted: list[dict] = []

    for c in candidates:
        c["status"] = "applied"
        rank = c.get("rank")
        score = float(c.get("composite_score") or 0)
        in_top = rank is not None and rank <= top_n
        above_min = score >= min_score

        if in_top or above_min:
            c["status"] = "shortlisted"
            c["shortlist_reason"] = (
                f"Top {top_n} (rank #{rank})" if in_top and not above_min
                else f"Score {score:.0%} >= {min_score:.0%}" if above_min and not in_top
                else f"Top {top_n} & score {score:.0%} >= {min_score:.0%}"
            )
            shortlisted.append(c)
        else:
            c.pop("shortlist_reason", None)

    return candidates, shortlisted
