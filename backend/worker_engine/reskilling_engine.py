def generate_reskilling_path(profile):
    role = profile["role"]

    if "bpo" in role.lower():
        return {
            "target_role": "AI Content Reviewer",
            "plan": [
                "Week 1-3: NPTEL Data Basics",
                "Week 4-5: SWAYAM AI Fundamentals",
                "Week 6-8: PMKVY Digital Marketing",
            ],
        }

    return {
        "target_role": "Data Analyst",
        "plan": [
            "Week 1-4: Python Basics",
            "Week 5-6: SQL",
            "Week 7-8: Dashboarding",
        ],
    }
