def parse_worker_profile(profile):
    writeup = profile["writeup"]

    skills = []

    if "excel" in writeup.lower():
        skills.append("excel")

    if "crm" in writeup.lower():
        skills.append("crm")

    if "customer" in writeup.lower():
        skills.append("customer_support")

    return {
        "role": profile["job_title"],
        "city": profile["city"],
        "experience": profile["experience_years"],
        "skills": skills,
    }
