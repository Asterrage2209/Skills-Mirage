import sqlite3
import json
import logging
from pathlib import Path
from chatbot.gemini_client import ask_gemini, generate_sql_query, generate_natural_response

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).resolve().parent.parent / "db" / "chat_data.db"

# ── Intent keywords ──────────────────────────────────────────────────────────

_RISK_KEYWORDS = [
    "risk score", "risk level", "why is my risk", "my risk",
    "risk increased", "risk high", "risk low", "risk moderate",
    "factors affect", "explain risk", "what affects my score",
    "vulnerability", "automation risk", "ai risk",
    "risk assessment", "risk analysis", "risk report",
    "why am i at risk", "high risk", "score explanation",
    # Hindi variants
    "jokhim", "risk kyun", "risk kyu", "mera risk",
]

_IMPROVEMENT_KEYWORDS = [
    "improve", "reduce risk", "lower risk", "reduce my risk",
    "what should i do", "what can i do", "next steps",
    "career direction", "career path", "future",
    "skills should i learn", "what to learn", "learn next",
    "how to upskill", "reskilling", "upskilling",
    "reskill", "upskill", "learning path", "course",
    "recommend", "suggestion", "guidance", "timeline",
    "how do i get better", "how to grow",
    # Hindi variants
    "kya seekhu", "kya karu", "kaise improve", "kaise sudhar",
    "sudhaar", "behtar", "seekhna", "path",
]


# ── Intent classifier ────────────────────────────────────────────────────────

def _classify_intent(question: str) -> str:
    """
    Return one of: 'risk_explanation', 'improvement_guidance', 'data_query'.
    Uses simple keyword matching — fast and deterministic.
    """
    q = question.lower()

    # Check improvement first (some questions mention "risk" AND "improve")
    if any(kw in q for kw in _IMPROVEMENT_KEYWORDS):
        return "improvement_guidance"

    if any(kw in q for kw in _RISK_KEYWORDS):
        return "risk_explanation"

    return "data_query"


# ── Handlers ─────────────────────────────────────────────────────────────────

def _handle_risk_explanation(question: str, user_data: dict) -> str:
    """Use the stored worker analysis / Gemini analysis to answer risk questions."""
    gemini_analysis = user_data.get("gemini_analysis") or {}
    job_role = user_data.get("job_role", "N/A")
    risk_score = gemini_analysis.get("risk_score")
    risk_level = gemini_analysis.get("risk_level", "unknown")
    explanation = gemini_analysis.get("explanation", "")
    pivot_roles = gemini_analysis.get("pivot_roles", [])
    new_skills = gemini_analysis.get("new_skills", [])

    if not gemini_analysis or risk_score is None:
        return (
            "I don't have a risk analysis on file for you yet. "
            "Please go to the **Worker Analysis** page, fill in your profile, "
            "and click 'Analyze Risk & Opportunities' first."
        )

    # Build a rich context and let Gemini compose a natural answer
    context = (
        f"The user's job role is '{job_role}'. "
        f"Their AI-risk score is {risk_score}/100 (level: {risk_level}). "
        f"Gemini explanation: {explanation}. "
        f"Suggested pivot roles: {', '.join(pivot_roles) if pivot_roles else 'none'}. "
        f"Recommended new skills: {', '.join(new_skills) if new_skills else 'none'}."
    )

    prompt = f"""You are a career guidance AI assistant. The user is asking about their AI-risk score.
Answer their question using ONLY the analysis data provided below. Be specific, reference their actual score
and factors. Be empathetic and helpful.

--- Analysis Data ---
{context}

--- User Question ---
{question}

Provide a clear, structured explanation. Do NOT say "I don't know" — use the data above.

LANGUAGE RULE (MANDATORY): Detect the language of the User Question above. Your ENTIRE response MUST be written in that SAME language.
- If the user wrote in English → reply ONLY in English.
- If the user wrote in Hindi → reply ONLY in Hindi.
Do NOT mix languages. Do NOT switch languages mid-response."""

    return ask_gemini(prompt)


def _handle_improvement_guidance(question: str, user_data: dict) -> str:
    """Use the stored reskilling result to answer improvement / career guidance questions."""
    reskilling = user_data.get("reskilling_result") or {}
    gemini_analysis = user_data.get("gemini_analysis") or {}
    job_role = user_data.get("job_role", "N/A")

    # Build context from both analyses
    risk_context = ""
    if gemini_analysis:
        risk_context = (
            f"Risk score: {gemini_analysis.get('risk_score', 'N/A')}/100 "
            f"(level: {gemini_analysis.get('risk_level', 'unknown')}). "
            f"Explanation: {gemini_analysis.get('explanation', '')}. "
            f"Pivot roles: {', '.join(gemini_analysis.get('pivot_roles', []))}. "
            f"New skills: {', '.join(gemini_analysis.get('new_skills', []))}."
        )

    reskilling_context = ""
    if reskilling and reskilling.get("recommendation_type"):
        reskilling_context = (
            f"\nRecommendation type: {reskilling.get('recommendation_type')}. "
            f"Summary: {reskilling.get('summary', '')}. "
            f"Recommended skills: {json.dumps(reskilling.get('recommended_skills', []), default=str)}. "
            f"Recommended courses: {json.dumps(reskilling.get('recommended_courses', [])[:8], default=str)}. "
            f"Recommended jobs: {json.dumps(reskilling.get('recommended_jobs', [])[:8], default=str)}. "
            f"Learning path: {json.dumps(reskilling.get('learning_path', []), default=str)}."
        )

    if not risk_context and not reskilling_context:
        return (
            "I don't have enough data to guide you yet. Please complete the following:\n\n"
            "1. Go to **Worker Analysis** and submit your profile.\n"
            "2. Go to **Reskilling Paths** and click 'Generate Reskilling Path'.\n\n"
            "Once done, come back and I'll provide personalised guidance!"
        )

    prompt = f"""You are a career guidance AI assistant. The user is asking for improvement advice or career direction.
Answer using ONLY the analysis and reskilling data provided below. Be specific — mention actual skills, courses,
jobs, and learning timelines from the data.

--- User Profile ---
Job role: {job_role}
Skills: {', '.join(user_data.get('skills', []))}

--- Risk Analysis ---
{risk_context if risk_context else 'Not available yet.'}

--- Reskilling Recommendations ---
{reskilling_context if reskilling_context else 'Not generated yet. Advise the user to generate a reskilling path.'}

--- User Question ---
{question}

Provide actionable, structured guidance. Include specific skill names, course names, and job titles from the data.
Do NOT say "I don't know" — use whatever data is available above.

LANGUAGE RULE (MANDATORY): Detect the language of the User Question above. Your ENTIRE response MUST be written in that SAME language.
- If the user wrote in English → reply ONLY in English.
- If the user wrote in Hindi → reply ONLY in Hindi.
Do NOT mix languages. Do NOT switch languages mid-response."""

    return ask_gemini(prompt)


# ── Database helpers (existing) ──────────────────────────────────────────────

def get_db_schema():
    if not DB_PATH.exists():
        return "No database found."
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table';")
    schema = "\n".join([row[0] for row in cursor.fetchall() if row[0]])
    conn.close()
    return schema

def clean_sql(sql_str):
    sql_str = sql_str.strip()
    if sql_str.startswith("```sql"):
        sql_str = sql_str[6:]
    if sql_str.startswith("```"):
        sql_str = sql_str[3:]
    if sql_str.endswith("```"):
        sql_str = sql_str[:-3]
    return sql_str.strip()


def _handle_data_query(question: str, worker_profile: dict) -> str:
    """Original NL → SQL → NL pipeline for job/course data questions."""
    schema = get_db_schema()
    if "No database found" in schema:
        return "Database missing. Please ask administrator to initialize."

    raw_sql = generate_sql_query(question, schema)
    sql = clean_sql(raw_sql)

    conn = sqlite3.connect(DB_PATH)
    if any(kw in sql.upper() for kw in ("DROP", "DELETE", "UPDATE", "INSERT")):
        conn.close()
        return "Query blocked due to safety restrictions."

    cursor = conn.cursor()
    cursor.execute(sql)
    results = cursor.fetchall()
    column_names = [desc[0] for desc in cursor.description] if cursor.description else []
    conn.close()

    formatted_results = "No records found matching the criteria."
    if results:
        sliced = results[:20]
        mapped = [{col: row[i] for i, col in enumerate(column_names)} for row in sliced]
        data_str = str(mapped)[:3000]
        if len(results) > 20:
            formatted_results = f"Found {len(results)} results (showing top 20):\n{data_str}"
        else:
            formatted_results = data_str

    return generate_natural_response(question, formatted_results, worker_profile)


# ── Main entry point ─────────────────────────────────────────────────────────

def handle_query(query: dict, user_data: dict | None = None) -> str:
    """
    Route a chatbot query based on detected intent.

    Args:
        query: dict with 'worker_profile' and 'question'
        user_data: authenticated user's MongoDB document (optional but needed
                   for risk/reskilling answers)
    """
    question = query.get("question", "")
    worker_profile = query.get("worker_profile", {})
    user_data = user_data or {}

    intent = _classify_intent(question)
    logger.info("Chatbot intent: %s | question: %s", intent, question[:80])

    if intent == "risk_explanation":
        return _handle_risk_explanation(question, user_data)

    if intent == "improvement_guidance":
        return _handle_improvement_guidance(question, user_data)

    # Default: NL → SQL → NL data query
    try:
        return _handle_data_query(question, worker_profile)
    except Exception as e:
        return f"Error processing query: {str(e)}"
