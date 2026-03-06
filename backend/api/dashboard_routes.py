import json
from pathlib import Path
from collections import Counter

from fastapi import APIRouter
from data.dataset_manager import get_all_jobs, get_latest_jobs
from intelligence.hiring_trends import compute_hiring_trends
from intelligence.skill_trends import compute_skill_trends
from intelligence.vulnerability_index import compute_vulnerability_index
from scrapers.naukri.naukri_scraper import run_scraper

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/stats")
def stats():
    jobs = get_all_jobs()
    total_jobs = len(jobs)
    
    city_counts = Counter()
    skill_counts = Counter()
    role_counts = Counter()
    
    for job in jobs:
        city_counts[job.get("city", "")] += 1
        for skill in job.get("skills", []):
            skill_counts[skill] += 1
        role_counts[job.get("title", "")] += 1
        
    top_city = city_counts.most_common(1)[0][0] if city_counts else "N/A"
    top_skill = skill_counts.most_common(1)[0][0] if skill_counts else "N/A"
    top_role = role_counts.most_common(1)[0][0] if role_counts else "N/A"
    
    return {
        "total_jobs": total_jobs,
        "top_city": top_city,
        "most_in_demand_skill": top_skill,
        "most_common_role": top_role
    }

@router.get("/hiring-trends")
def hiring_trends():
    return compute_hiring_trends()

@router.get("/skill-trends")
def skill_trends():
    return compute_skill_trends()

@router.get("/vulnerability")
def vulnerability():
    return compute_vulnerability_index()

@router.get("/latest-jobs")
def latest_jobs():
    return get_latest_jobs(50)

@router.get("/scraped-jobs")
def scraped_jobs(refresh: bool = True):
    scrape_error = None
    stats = None
    if refresh:
        try:
            stats = run_scraper()
        except Exception as exc:
            scrape_error = str(exc)

    return {
        "total": len(get_all_jobs()),
        "jobs": [],
        "scrape_error": scrape_error,
        "scrape_stats": stats,
    }

@router.get("/top-cities")
def top_cities():
    jobs = get_all_jobs()
    counts = Counter(job.get("city", "") for job in jobs if job.get("city"))
    return [{"name": city, "demand": count} for city, count in counts.most_common(10)]

@router.get("/industry-distribution")
def industry_distribution():
    jobs = get_all_jobs()
    # Using company as industry proxy, or parse if needed.
    counts = Counter(str(job.get("company", "Unknown")).strip() for job in jobs)
    return [{"name": ind, "value": count} for ind, count in counts.most_common(5) if ind]

@router.get("/top-roles")
def top_roles():
    jobs = get_all_jobs()
    counts = Counter(str(job.get("title", "")).strip() for job in jobs if job.get("title"))
    return [{"role": role, "count": count} for role, count in counts.most_common(10)]
