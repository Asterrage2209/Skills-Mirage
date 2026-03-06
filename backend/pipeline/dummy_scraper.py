from datetime import datetime


def get_dummy_jobs():
    return [
        {
            "title": "BPO Voice Executive",
            "city": "Pune",
            "skills": ["customer support", "crm", "excel"],
            "description": "Handle inbound calls and resolve customer issues",
            "ai_mentions": False,
            "date": "2025-12-01",
        },
        {
            "title": "AI Content Reviewer",
            "city": "Pune",
            "skills": ["content moderation", "ai tools", "quality review"],
            "description": "Review AI generated content",
            "ai_mentions": True,
            "date": "2025-12-05",
        },
        {
            "title": "Data Analyst",
            "city": "Indore",
            "skills": ["python", "sql", "excel"],
            "description": "Analyze data and build dashboards",
            "ai_mentions": True,
            "date": "2025-12-10",
        },
    ]
