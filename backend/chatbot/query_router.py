from chatbot.prompt_builder import build_prompt
from chatbot.gemini_client import ask_gemini


def handle_query(query):
    prompt = build_prompt(query)

    response = ask_gemini(prompt)

    return response
