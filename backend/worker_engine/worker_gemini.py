import os
import json
import re
import logging
from dotenv import load_dotenv
from google import genai

load_dotenv()
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """you will be given 4 inputs which are current job title, city, years of experience and user's known skills. you will have to calculate the risk score which is risk of ai taking over your job. if the risk score is very high, you will have to suggest pivot roles so the user gets a role based on the given skills. if the risk score is moderate, you will have to suggest more skills which can reduce the risk score. if the risk score is less then no worries of ai taking your jobs. the formula of risk score is such : Risk Score Formula
Risk = Base Risk + (Regional Adjust × 0.1) - (Exp Reduction) + (Entry Penalty)
• Base Risk: Calculated from role automation vulnerability.
• Exp Reduction: Up to 25 points reduction based on years of tenure.
• Entry Penalty: 15 point addition for users with < 1 year experience.

Pivot Role Logic

Our engine identifies transition paths by mapping current operational fatigue to AI-resilient growth roles. BPO profiles are prioritized for AI Content Moderation, while general roles pivot toward Data Analytics.

the output should be of the form : pivot roles and new skills to add.

IMPORTANT: You MUST respond ONLY with valid JSON in this exact format, no extra text:
{
  "risk_score": <number between 0-100>,
  "risk_level": "<high|moderate|low>",
  "pivot_roles": ["role1", "role2"],
  "new_skills": ["skill1", "skill2"],
  "explanation": "brief explanation of the assessment"
}
"""


def analyze_worker(job_title: str, city: str, experience: float, skills: list[str]) -> dict:
    """
    Call Gemini with user inputs to get AI risk assessment,
    pivot roles, and new skills suggestions.
    """
    api_key = os.getenv("GEMINI_API_KEY_WORKERANALYSIS")
    if not api_key:
        logger.error("GEMINI_API_KEY_WORKERANALYSIS is not set")
        return {
            "risk_score": None,
            "risk_level": "unknown",
            "pivot_roles": [],
            "new_skills": [],
            "explanation": "Gemini worker analysis is not configured. Set GEMINI_API_KEY_WORKERANALYSIS.",
            "raw_response": "",
        }

    # Build user input section
    user_input = (
        f"Current Job Title: {job_title}\n"
        f"City: {city}\n"
        f"Years of Experience: {experience}\n"
        f"Known Skills: {', '.join(skills) if skills else 'None provided'}"
    )

    full_prompt = f"{SYSTEM_PROMPT}\n\nUser Inputs:\n{user_input}"

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_prompt,
        )
        raw_text = response.text or ""
        logger.info("Gemini worker analysis raw response: %s", raw_text[:300])
    except Exception as exc:
        logger.error("Gemini worker analysis request failed: %s", exc)
        return {
            "risk_score": None,
            "risk_level": "unknown",
            "pivot_roles": [],
            "new_skills": [],
            "explanation": f"Gemini request failed: {exc}",
            "raw_response": "",
        }

    # Parse the JSON response from Gemini
    return _parse_gemini_response(raw_text)


def _parse_gemini_response(raw_text: str) -> dict:
    """Extract structured data from Gemini's response."""
    default = {
        "risk_score": None,
        "risk_level": "unknown",
        "pivot_roles": [],
        "new_skills": [],
        "explanation": "",
        "raw_response": raw_text,
    }

    try:
        # Try to extract JSON from the response (Gemini may wrap it in markdown)
        json_match = re.search(r'\{[\s\S]*\}', raw_text)
        if json_match:
            data = json.loads(json_match.group())
            return {
                "risk_score": data.get("risk_score"),
                "risk_level": data.get("risk_level", "unknown"),
                "pivot_roles": data.get("pivot_roles", []),
                "new_skills": data.get("new_skills", []),
                "explanation": data.get("explanation", ""),
                "raw_response": raw_text,
            }
    except (json.JSONDecodeError, AttributeError) as exc:
        logger.warning("Failed to parse Gemini JSON response: %s", exc)

    # Fallback: return raw text as explanation
    default["explanation"] = raw_text
    return default
