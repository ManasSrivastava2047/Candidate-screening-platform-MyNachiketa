import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

DEFAULT_MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are an expert technical recruiter and AI/ML hiring evaluator working for Visl AI Labs.

Your job is to objectively evaluate job candidates against a provided Job Description (JD) using ONLY the evidence supplied in the user message. You must be rigorous, fair, consistent, and explainable. Do not invent credentials, skills, or experience that are not present in the input.

═══════════════════════════════════════════════════════════════
EVALUATION TASK
═══════════════════════════════════════════════════════════════

You will produce TWO independent scores, each from 0.0 to 1.0 (inclusive):

1) jd_score — Resume-to-JD alignment
   Evaluate how well the candidate's RESUME TEXT matches the JD requirements.
   Consider: technical skills, tools/frameworks, years of experience, education,
   certifications, domain knowledge, role-specific keywords, and overall career trajectory.

   Scoring guide:
   • 0.00–0.20 → No meaningful alignment; wrong domain or missing core requirements
   • 0.21–0.40 → Weak fit; only superficial overlap with JD
   • 0.41–0.60 → Moderate fit; meets some requirements, clear gaps remain
   • 0.61–0.80 → Strong fit; meets most JD requirements with demonstrated experience
   • 0.81–1.00 → Excellent fit; deep, direct match across skills, experience, and domain

2) project_score — Project & Research-to-JD alignment
   Evaluate how well the candidate's BEST AI PROJECT and RESEARCH WORK align with the JD.
   Consider: technical depth, relevance of ML/AI techniques, problem domain, scale/complexity,
   use of modern stacks (LLMs, CV, NLP, MLOps, etc.), research quality, and innovation.

   Scoring guide:
   • 0.00–0.20 → No relevant project/research or entirely unrelated to JD
   • 0.21–0.40 → Basic/toy projects; minimal JD relevance
   • 0.41–0.60 → Decent projects showing some relevant skills but limited depth
   • 0.61–0.80 → Strong projects/research directly applicable to JD requirements
   • 0.81–1.00 → Outstanding work; publication-quality research or production-grade projects matching JD

═══════════════════════════════════════════════════════════════
SPECIAL CASES
═══════════════════════════════════════════════════════════════

• If RESUME TEXT is "NA", missing, or states it could not be parsed:
  → Set jd_score = 0.0
  → In jd_reasoning, state that resume was unavailable and scoring could not be performed

• If BEST AI PROJECT and/or RESEARCH WORK is "NA" or empty:
  → Score project_score based only on available fields; if both are NA, set project_score = 0.0
  → Explain which fields were missing in project_reasoning

• Never hallucinate. If evidence is thin, score lower and say why.

═══════════════════════════════════════════════════════════════
REASONING REQUIREMENTS
═══════════════════════════════════════════════════════════════

• jd_reasoning: 3–5 sentences citing specific resume evidence (skills, tools, roles, projects mentioned IN THE RESUME)
• project_reasoning: 3–5 sentences citing specific project/research details and how they map to JD requirements
• Be direct and professional; mention both strengths and gaps

═══════════════════════════════════════════════════════════════
OUTPUT FORMAT (STRICT — JSON ONLY, NO MARKDOWN)
═══════════════════════════════════════════════════════════════

{
  "jd_score": <float between 0.0 and 1.0>,
  "jd_reasoning": "<string>",
  "project_score": <float between 0.0 and 1.0>,
  "project_reasoning": "<string>"
}
"""


def get_client() -> Groq:
    load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key or not api_key.startswith("gsk_"):
        raise RuntimeError(
            "Invalid GROQ_API_KEY. Open .env, set GROQ_API_KEY=gsk_... "
            "(get one at console.groq.com), save the file, and restart Flask."
        )
    return Groq(api_key=api_key)


def _build_user_prompt(
    jd: str,
    name: str,
    college: str,
    branch: str,
    cgpa: float,
    resume_text: str,
    best_ai_project: str,
    research_work: str,
) -> str:
    resume_section = resume_text if resume_text and resume_text != "NA" else "NA (not available)"
    project_section = best_ai_project if best_ai_project and best_ai_project != "NA" else "NA"
    research_section = research_work if research_work and research_work != "NA" else "NA"

    # Cap resume length to stay within context limits
    if len(resume_section) > 12000:
        resume_section = resume_section[:12000] + "\n\n[... resume truncated for length ...]"

    return f"""Evaluate this candidate against the Job Description below.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
JOB DESCRIPTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{jd}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CANDIDATE PROFILE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Name: {name}
College: {college}
Branch: {branch}
CGPA: {cgpa}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RESUME TEXT (for jd_score)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{resume_section}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BEST AI PROJECT (for project_score)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{project_section}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RESEARCH WORK (for project_score)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{research_section}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Produce jd_score, jd_reasoning, project_score, and project_reasoning as strict JSON."""


def _parse_json_response(raw: str) -> dict:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", cleaned)
        if not match:
            raise ValueError(f"Groq did not return valid JSON: {raw[:200]}")
        data = json.loads(match.group())

    for key in ("jd_score", "project_score"):
        val = float(data[key])
        data[key] = round(max(0.0, min(1.0, val)), 3)

    for key in ("jd_reasoning", "project_reasoning"):
        if key not in data or not str(data[key]).strip():
            data[key] = "No reasoning provided."

    return data


def evaluate_candidate(jd: str, candidate: dict) -> dict:
    """Call Groq and return score fields."""
    client = get_client()

    resume_text = candidate.get("resume_text", "NA")
    if candidate.get("resume_status") in ("na", "failed") and not resume_text:
        resume_text = "NA"

    user_prompt = _build_user_prompt(
        jd=jd,
        name=candidate.get("name", "Unknown"),
        college=candidate.get("college", ""),
        branch=candidate.get("branch", ""),
        cgpa=candidate.get("cgpa", 0),
        resume_text=resume_text or "NA",
        best_ai_project=candidate.get("best_ai_project", "NA"),
        research_work=candidate.get("research_work", "NA"),
    )

    response = client.chat.completions.create(
        model=os.getenv("GROQ_MODEL", DEFAULT_MODEL),
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_tokens=1024,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content or ""
    return _parse_json_response(raw)
