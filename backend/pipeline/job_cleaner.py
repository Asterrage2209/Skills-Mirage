from datetime import datetime

def clean_jobs(jobs):
    cleaned = []
    today_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S +0000")
    
    for job in jobs:
        # map scraped fields to dataset schema fields
        cleaned_job = {
            "jobtitle": job.get("title") or job.get("query_role") or "",
            "company": job.get("company", ""),
            "industry": "",  
            "joblocation_address": job.get("location") or job.get("query_city") or "",
            "experience": job.get("experience", ""),
            "postdate": today_str,
            "jobdescription": job.get("description", ""),
            "skills": job.get("skills", [])
        }
        cleaned.append(cleaned_job)
        
    return cleaned
