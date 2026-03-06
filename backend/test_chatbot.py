import os
from pathlib import Path
from dotenv import load_dotenv

# Ensure dotenv is loaded
load_dotenv(Path(__file__).resolve().parent / ".env")

from chatbot.query_router import handle_query

def test_chatbot_query():
    query = {
        "worker_profile": {
            "skills": ["python", "data science"],
            "experience": "2 years",
            "preferred_location": "Bangalore"
        },
        "question": "Can you find me some jobs that match my profile? Mere skills python aur data science hain."
    }
    
    print("Testing Query Router...")
    response = handle_query(query)
    
    print("\n--- Response ---")
    print(response)

if __name__ == "__main__":
    test_chatbot_query()
