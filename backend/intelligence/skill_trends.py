from collections import Counter
from data.dataset_manager import get_all_jobs, get_all_courses

def _extract_year(postdate_value):
    postdate = str(postdate_value or "").strip()
    if len(postdate) >= 4 and postdate[:4].isdigit():
        return int(postdate[:4])
    return None


def get_available_job_years():
    jobs = get_all_jobs()
    years = []
    for job in jobs:
        year = _extract_year(job.get("postdate", ""))
        if year is not None:
            years.append(year)
    return sorted(set(years), reverse=True)


def compute_skill_trends(year=None):
    jobs = get_all_jobs()

    if year is not None:
        jobs = [job for job in jobs if _extract_year(job.get("postdate", "")) == year]

    if not jobs:
        return {
            "rising_skills": [],
            "declining_skills": []
        }
    
    # Split jobs into older and newer halves (assuming sorted by postdate or just by index)
    # Actually dataset_manager preserves sequential index, but scraping appends to end.
    # So newer is at the end.
    midpoint = max(1, len(jobs) // 2)
    previous_group = jobs[:midpoint]
    recent_group = jobs[midpoint:]
    
    def get_counts(group):
        c = Counter()
        for j in group:
            c.update(j["skills"])
        return c
        
    prev_counts = get_counts(previous_group)
    rec_counts = get_counts(recent_group)
    
    all_skills = set(prev_counts.keys()).union(rec_counts.keys())
    trends = []
    for skill in all_skills:
        change = rec_counts.get(skill, 0) - prev_counts.get(skill, 0)
        trends.append({"skill": skill, "change": change})
        
    trends.sort(key=lambda x: x["change"], reverse=True)
    
    rising = [{"name": t["skill"], "growth": f'+{t["change"]}', "color": "from-blue-500 to-cyan-400"} for t in trends[:10] if t["change"] > 0]
    declining = [{"name": t["skill"], "decline": str(t["change"])} for t in trends[-10:] if t["change"] < 0]
    
    return {
        "rising_skills": rising,
        "declining_skills": declining
    }

def compute_skill_gap():
    jobs = get_all_jobs()
    courses = get_all_courses()
    
    job_skill_count = Counter()
    for job in jobs:
        for sk in job.get("skills", []):
            job_skill_count[sk.lower()] += 1
            
    course_skill_count = Counter()
    for course in courses:
        for tag in course.get("skill_tags", []):
            course_skill_count[tag.lower()] += 1
            
    gap_metrics = []
    
    for skill, demand in job_skill_count.items():
        supply = course_skill_count.get(skill, 0)
        gap = demand - supply
        gap_metrics.append({
            "skill": skill,
            "market_demand": demand,
            "training_supply": supply,
            "gap": gap
        })
        
    # Sort strictly by highest demand gap
    gap_metrics = sorted(gap_metrics, key=lambda x: x["gap"], reverse=True)
    
    return gap_metrics[:10]
