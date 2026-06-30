import json
import os
import re

from utils.evaluate import get_client
from utils.github import build_github_summary, extract_username

DEFAULT_MODEL = "llama-3.3-70b-versatile"

GITHUB_SYSTEM = """You are an expert technical recruiter evaluating a candidate's GitHub profile for Visl AI Labs.

Score github_score from 0.0 to 1.0 based on:
- Project complexity and code diversity (languages, frameworks)
- Relevance of repositories to the Job Description
- Stars, forks, activity signals (proxy for quality)
- Consistency of contributions (multiple meaningful repos vs empty profiles)
- AI/ML/engineering depth visible in repo names, descriptions, topics

Scoring guide:
• 0.00–0.20 → No meaningful repos or entirely unrelated to JD
• 0.21–0.40 → Few/basic repos, weak JD relevance
• 0.41–0.60 → Some solid repos with partial JD alignment
• 0.61–0.80 → Strong repos clearly relevant to JD skills
• 0.81–1.00 → Exceptional portfolio directly matching JD requirements

If GitHub data is unavailable, set github_score = 0.0 and explain why.

github_reasoning: 3–5 sentences citing specific repos, languages, and JD alignment.

Respond with strict JSON only:
{"github_score": <float>, "github_reasoning": "<string>"}
"""


def _parse_github_json(raw: str) -> dict:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", cleaned)
        if not match:
            raise ValueError(f"Invalid JSON from Groq: {raw[:200]}")
        data = json.loads(match.group())
    score = round(max(0.0, min(1.0, float(data["github_score"]))), 3)
    reasoning = str(data.get("github_reasoning", "")).strip() or "No reasoning provided."
    return {"github_score": score, "github_reasoning": reasoning}


def evaluate_github(jd: str, candidate: dict, github_data: dict) -> dict:
    client = get_client()
    repos_text = "\n".join(
        f"- {r['name']}: {r['description'][:200]} | lang={r['language']} | "
        f"stars={r['stars']} forks={r['forks']} | topics={', '.join(r['topics'][:5])}"
        for r in github_data.get("repos", [])
    ) or "No repositories found."

    user_prompt = f"""JOB DESCRIPTION:
{jd}

CANDIDATE: {candidate.get('name')} ({github_data.get('username')})
Public repos: {github_data.get('public_repos')}
Followers: {github_data.get('followers')}
Bio: {github_data.get('bio')}
Top languages: {', '.join(github_data.get('top_languages', []))}

REPOSITORIES:
{repos_text}

Produce github_score and github_reasoning as JSON."""

    response = client.chat.completions.create(
        model=os.getenv("GROQ_MODEL", DEFAULT_MODEL),
        messages=[
            {"role": "system", "content": GITHUB_SYSTEM},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_tokens=768,
        response_format={"type": "json_object"},
    )
    return _parse_github_json(response.choices[0].message.content or "")


def analyze_candidate_github(jd: str, candidate: dict) -> dict:
    github_url = candidate.get("github", "NA")
    if github_url == "NA" or "github" in candidate.get("na_fields", []):
        return {
            "github_score": 0.0,
            "github_reasoning": "No GitHub profile available.",
            "github_status": "na",
        }

    username = extract_username(github_url)
    if not username:
        return {
            "github_score": 0.0,
            "github_reasoning": "Invalid GitHub URL.",
            "github_status": "failed",
            "github_error": "Could not extract username",
        }

    try:
        data = build_github_summary(username)
        candidate["github_data"] = data
        scores = evaluate_github(jd, candidate, data)
        scores["github_status"] = "ok"
        return scores
    except Exception as exc:
        return {
            "github_score": 0.0,
            "github_reasoning": f"GitHub analysis failed: {exc}",
            "github_status": "failed",
            "github_error": str(exc),
        }
