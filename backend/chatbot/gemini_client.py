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
            model="gemini-2.0-flash",
            contents=prompt,
        )
    except Exception as exc:
        return f"Gemini request failed: {exc}"

    return response.text or "No response text returned by Gemini."
