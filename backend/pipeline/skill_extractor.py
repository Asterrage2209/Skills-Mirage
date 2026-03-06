def extract_skills(jobs):
    for job in jobs:
        skills = job.get("skills", [])
        if not isinstance(skills, list):
            skills = [s.strip() for s in str(skills).split(",") if s.strip()]
        job["skills"] = skills
    return jobs
