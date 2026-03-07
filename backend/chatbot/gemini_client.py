import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

def ask_gemini(prompt):
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return "Gemini is not configured. Set GEMINI_API_KEY and try again."

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
    except Exception as exc:
        return f"Gemini request failed: {exc}"

    return response.text or "No response text returned by Gemini."

def generate_sql_query(user_prompt, schema_definition):
    prompt = f"""
    You are an AI that converts natural language to SQL queries. The queries should be safe to read-only queries against SQLite.
    You will only respond with the SQL query and nothing else. Do not use Markdown formatting for the code block.

    Given the following database schema:
    {schema_definition}
    
    Translate the user's question, which may be in English or Hindi, into a valid SQLite query.
    Return ONLY the raw SQL query.
    
    User Question: {user_prompt}
    """
    return ask_gemini(prompt)

def generate_natural_response(user_prompt, sql_results, worker_profile=None):
    prompt = f"""
    You are an AI assistant that provides answers based on database results. You are answering a user querying job/course datasets.
    Respond in a natural, helpful, and conversational tone.
    
    Worker Profile context (use if relevant to personalize answer):
    {worker_profile if worker_profile else "Not provided"}

    User Question:
    {user_prompt}

    Database Execution Results (JSON format):
    {sql_results}

    Provide a concise, human-friendly summary of the results. Only mention data that actually exists in the results.

    LANGUAGE RULE (MANDATORY): Detect the language of the User Question above. Your ENTIRE response MUST be written in that SAME language.
    - If the user wrote in English → reply ONLY in English.
    - If the user wrote in Hindi → reply ONLY in Hindi.
    Do NOT mix languages. Do NOT switch languages mid-response.
    """
    return ask_gemini(prompt)
