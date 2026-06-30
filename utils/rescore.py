from utils.composite import rank_candidates

FINAL_TOP_N = 5
FINAL_MIN_SCORE = 0.6

PIPELINE_STATUSES = frozenset({"shortlisted", "test_sent", "interview"})


def apply_final_ranking(candidates: list[dict]) -> tuple[list[dict], list[dict]]:
    """Re-score with test results, re-rank, and mark interview qualifiers."""
    ranked = rank_candidates(candidates)
    interview: list[dict] = []

    for c in ranked:
        if c.get("test_results_status") != "ok":
            continue
        if c.get("status") not in PIPELINE_STATUSES:
            continue

        rank = c.get("rank")
        score = float(c.get("composite_score") or 0)
        in_top = rank is not None and rank <= FINAL_TOP_N
        above_min = score >= FINAL_MIN_SCORE

        if in_top or above_min:
            c["status"] = "interview"
            if in_top and above_min:
                c["interview_reason"] = f"Rank #{rank} & score {score:.0%} >= {FINAL_MIN_SCORE:.0%}"
            elif in_top:
                c["interview_reason"] = f"Top {FINAL_TOP_N} (rank #{rank})"
            else:
                c["interview_reason"] = f"Final score {score:.0%} >= {FINAL_MIN_SCORE:.0%}"
            interview.append(c)
        else:
            c.pop("interview_reason", None)

    return ranked, interview
