import re

TECH_BRANCH_KEYWORDS = {
    "computer", "cse", "cs", "it", "ai", "ml", "data", "software",
    "information", "electronics", "ece", "eee", "physics", "mathematics",
    "statistics", "robotics", "bioinformatics",
}

JD_TECH_SIGNALS = (
    "machine learning", "artificial intelligence", "deep learning",
    "python", "software", "data science", "computer", "engineering",
    "ai", "ml", "nlp", "computer vision",
)


def _tokenize(text: str) -> set[str]:
    return {t for t in re.split(r"[\s/,&\-]+", text.lower()) if len(t) > 2}


def relevance_bonus(jd: str, college: str, branch: str) -> tuple[float, list[str]]:
    """Up to +0.10 bonus for college/branch alignment with the JD."""
    if not jd.strip():
        return 0.0, []

    jd_lower = jd.lower()
    notes: list[str] = []
    bonus = 0.0

    branch_lower = (branch or "").lower()
    branch_tokens = _tokenize(branch_lower)
    for token in branch_tokens:
        if token in jd_lower:
            bonus += 0.05
            notes.append(f"Branch '{branch}' matches JD keywords")
            break

    if any(sig in jd_lower for sig in JD_TECH_SIGNALS):
        if branch_tokens & TECH_BRANCH_KEYWORDS:
            bonus += 0.05
            notes.append(f"Technical branch '{branch}' is relevant to the role")

    college_lower = (college or "").lower()
    for word in [w for w in college_lower.split() if len(w) > 4][:4]:
        if word in jd_lower:
            bonus += 0.03
            notes.append(f"College '{college}' aligns with JD")
            break

    return min(0.10, bonus), notes


def score_candidate_academic(jd: str, candidate: dict) -> dict:
    try:
        cgpa = float(candidate.get("cgpa", 0))
    except (TypeError, ValueError):
        return {
            "cgpa_score": 0.0,
            "academic_reasoning": "Invalid CGPA value.",
            "academic_status": "failed",
            "academic_error": "Invalid CGPA",
        }

    if not (0 <= cgpa <= 10):
        return {
            "cgpa_score": 0.0,
            "academic_reasoning": f"CGPA {cgpa} is outside the valid 0–10 range.",
            "academic_status": "failed",
            "academic_error": "CGPA out of range",
        }

    base = round(cgpa / 10, 3)
    bonus, notes = relevance_bonus(jd, candidate.get("college", ""), candidate.get("branch", ""))
    final = round(min(1.0, base + bonus), 3)

    parts = [f"Base score: {cgpa}/10 = {base:.2f}."]
    if notes:
        parts.append(f"Relevance bonus: +{bonus:.2f} ({'; '.join(notes)}).")
    else:
        parts.append("No college/branch relevance bonus applied.")
    parts.append(f"Final academic score: {final:.2f}.")

    return {
        "cgpa_score": final,
        "academic_reasoning": " ".join(parts),
        "academic_status": "ok",
    }
