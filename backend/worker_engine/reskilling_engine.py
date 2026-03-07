"""
Gemini-powered reskilling engine.

Uses hiring trend data from naukri_jobs.csv and course data from courses.csv
to build a rich context prompt, then asks Gemini to produce personalised
reskilling / upskilling recommendations.
"""

import os
import json
import re
import logging
from dotenv import load_dotenv
from google import genai

from data.dataset_manager import get_all_jobs, get_all_courses
from intelligence.skill_trends import compute_skill_trends

load_dotenv()
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt template
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a career guidance AI. You will receive:
1. A worker's current profile (job title, city, experience, skills).
2. Their AI-risk assessment (risk_score 0-100, risk_level, pivot_roles, new_skills).
3. Market hiring trends: rising skills and declining skills with growth numbers.
4. A list of available training courses (with name, source, url, duration, skill_tags).
5. A list of relevant job openings (with title, company, location, skills).

Your task:
- If the worker's current field has INCREASING hiring demand → recommend UPSKILLING
  (deeper skills in the same domain).
- If the worker's current field has DECLINING hiring demand → recommend RESKILLING
  (transition skills from growing fields).
- For every recommended skill, match it to courses from the provided course list.
- Match the worker's existing + recommended skills to jobs from the provided job list.
- Generate a realistic weekly learning path / timeline.

IMPORTANT: Respond ONLY with valid JSON in this exact format, no extra text:
{
  "recommendation_type": "upskilling" or "reskilling",
  "summary": "Brief 2-3 sentence explanation of the recommendation strategy.",
  "recommended_skills": [
    {"skill": "skill name", "reason": "why this skill is recommended"}
  ],
  "recommended_courses": [
    {
      "name": "course name",
      "source": "NPTEL/SWAYAM/etc",
      "url": "course url",
      "duration": "duration string",
      "matched_skills": ["skill1", "skill2"]
    }
  ],
  "recommended_jobs": [
    {
      "title": "job title",
      "company": "company name",
      "location": "city",
      "required_skills": ["skill1", "skill2"],
      "match_reason": "why this job is a good fit"
    }
  ],
  "learning_path": [
    {
      "week": "Week 1-2",
      "title": "Step title",
      "description": "What to learn and do in this period."
    }
  ]
}
"""


# ---------------------------------------------------------------------------
# Helper: gather relevant courses
# ---------------------------------------------------------------------------
def _find_matching_courses(target_skills: list[str], max_courses: int = 30) -> list[dict]:
    """Return courses whose skill_tags overlap with *target_skills*."""
    courses = get_all_courses()
    target_lower = {s.lower().strip() for s in target_skills if s}

    scored: list[tuple[int, dict]] = []
    for c in courses:
        tags = c.get("skill_tags", [])
        if isinstance(tags, str):
            tags = [t.strip().lower() for t in tags.split(",") if t.strip()]
        overlap = len(target_lower.intersection({t.lower() for t in tags}))
        if overlap > 0:
            scored.append((overlap, c))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [
        {
            "name": c.get("name", ""),
            "source": c.get("source", ""),
            "url": c.get("url", ""),
            "duration": c.get("duration", ""),
            "skill_tags": ", ".join(c.get("skill_tags", [])),
        }
        for _, c in scored[:max_courses]
    ]


# ---------------------------------------------------------------------------
# Helper: gather relevant jobs
# ---------------------------------------------------------------------------
def _find_matching_jobs(target_skills: list[str], max_jobs: int = 20) -> list[dict]:
    """Return jobs whose required skills overlap with *target_skills*."""
    jobs = get_all_jobs()
    target_lower = {s.lower().strip() for s in target_skills if s}

    scored: list[tuple[int, dict]] = []
    for j in jobs:
        job_skills = j.get("skills", [])
        if isinstance(job_skills, str):
            job_skills = [s.strip().lower() for s in job_skills.split(",") if s.strip()]
        overlap = len(target_lower.intersection({s.lower() for s in job_skills}))
        if overlap > 0:
            scored.append((overlap, j))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [
        {
            "title": j.get("jobtitle", j.get("title", "")),
            "company": j.get("company", ""),
            "location": j.get("city", j.get("joblocation_address", "")),
            "skills": ", ".join(j.get("skills", [])[:10]),
        }
        for _, j in scored[:max_jobs]
    ]


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def generate_reskilling_path(
    job_title: str,
    city: str,
    experience: float,
    skills: list[str],
    gemini_analysis: dict | None = None,
) -> dict:
    """
    Build a context-rich prompt from live datasets and call Gemini to produce
    a personalised reskilling / upskilling plan.
    """
    api_key = os.getenv("GEMINI_API_KEY_RESKILLING")
    if not api_key:
        logger.error("GEMINI_API_KEY_RESKILLING is not set")
        return _error_response("Gemini reskilling is not configured. Set GEMINI_API_KEY_RESKILLING.")

    # ── 1. Hiring trends ────────────────────────────────────────────────
    trends = compute_skill_trends()
    rising = trends.get("rising_skills", [])[:10]
    declining = trends.get("declining_skills", [])[:10]

    # ── 2. Combine skill pool for course & job search ───────────────────
    extra_skills: list[str] = []
    if gemini_analysis:
        extra_skills += gemini_analysis.get("new_skills", [])
        extra_skills += gemini_analysis.get("pivot_roles", [])
    extra_skills += [r.get("name", "") for r in rising]
    all_target_skills = list(set(skills + extra_skills))

    # ── 3. Pull matching courses & jobs ─────────────────────────────────
    matched_courses = _find_matching_courses(all_target_skills)
    matched_jobs = _find_matching_jobs(all_target_skills)

    # ── 4. Build prompt ─────────────────────────────────────────────────
    user_section = (
        f"Current Job Title: {job_title}\n"
        f"City: {city}\n"
        f"Years of Experience: {experience}\n"
        f"Known Skills: {', '.join(skills) if skills else 'None provided'}\n"
    )

    risk_section = ""
    if gemini_analysis:
        risk_section = (
            f"\n--- AI Risk Assessment ---\n"
            f"Risk Score: {gemini_analysis.get('risk_score', 'N/A')}/100\n"
            f"Risk Level: {gemini_analysis.get('risk_level', 'unknown')}\n"
            f"Pivot Roles Suggested: {', '.join(gemini_analysis.get('pivot_roles', []))}\n"
            f"New Skills Suggested: {', '.join(gemini_analysis.get('new_skills', []))}\n"
            f"Explanation: {gemini_analysis.get('explanation', '')}\n"
        )

    trends_section = (
        f"\n--- Market Hiring Trends ---\n"
        f"Rising Skills: {json.dumps(rising, default=str)}\n"
        f"Declining Skills: {json.dumps(declining, default=str)}\n"
    )

    courses_section = (
        f"\n--- Available Training Courses (matched to target skills) ---\n"
        f"{json.dumps(matched_courses[:20], indent=2, default=str)}\n"
    )

    jobs_section = (
        f"\n--- Relevant Job Openings (matched to target skills) ---\n"
        f"{json.dumps(matched_jobs[:15], indent=2, default=str)}\n"
    )

    full_prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"--- Worker Profile ---\n{user_section}"
        f"{risk_section}"
        f"{trends_section}"
        f"{courses_section}"
        f"{jobs_section}"
    )

    # ── 5. Call Gemini ──────────────────────────────────────────────────
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_prompt,
        )
        raw_text = response.text or ""
        logger.info("Gemini reskilling raw response (first 300 chars): %s", raw_text[:300])
    except Exception as exc:
        logger.error("Gemini reskilling request failed: %s", exc)
        return _error_response(f"Gemini request failed: {exc}")

    # ── 6. Parse response ───────────────────────────────────────────────
    return _parse_response(raw_text)


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------
def _parse_response(raw_text: str) -> dict:
    """Extract structured JSON from Gemini's response."""
    default = _error_response("Could not parse Gemini response.")
    default["raw_response"] = raw_text

    try:
        json_match = re.search(r"\{[\s\S]*\}", raw_text)
        if json_match:
            data = json.loads(json_match.group())
            return {
                "recommendation_type": data.get("recommendation_type", "reskilling"),
                "summary": data.get("summary", ""),
                "recommended_skills": data.get("recommended_skills", []),
                "recommended_courses": data.get("recommended_courses", []),
                "recommended_jobs": data.get("recommended_jobs", []),
                "learning_path": data.get("learning_path", []),
                "raw_response": raw_text,
                "error": None,
            }
    except (json.JSONDecodeError, AttributeError) as exc:
        logger.warning("Failed to parse Gemini reskilling JSON: %s", exc)

    default["summary"] = raw_text
    return default


def _error_response(message: str) -> dict:
    return {
        "recommendation_type": None,
        "summary": message,
        "recommended_skills": [],
        "recommended_courses": [],
        "recommended_jobs": [],
        "learning_path": [],
        "raw_response": "",
        "error": message,
    }
