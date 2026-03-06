import json
from pathlib import Path
from collections import Counter

from fastapi import APIRouter
from data.dataset_manager import get_all_jobs, get_latest_jobs
from intelligence.hiring_trends import compute_hiring_trends
from intelligence.skill_trends import compute_skill_trends, compute_skill_gap
from intelligence.vulnerability_index import compute_vulnerability_index
from scrapers.naukri.naukri_scraper import run_scraper
from db.mongo import users_collection
import logging

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/skill-gap")
def skill_gap():
    return compute_skill_gap()

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
    jobs = get_all_jobs()
    vuln_data = compute_vulnerability_index()
    role_risks = vuln_data.get("role_risks", {})
    
    unique_roles = {}
    for job in jobs:
        role = str(job.get("title", "")).strip().lower()
        city = str(job.get("city", "Unknown")).strip()
        if not role:
            continue
        
        key = (role, city)
        if key not in unique_roles:
            score = role_risks.get(role, 0)
            unique_roles[key] = {
                "job_role": role.title(),
                "city": city.title(),
                "ai_risk_score": round(score)
            }
                
    logging.info(f"Unique roles generated: {len(unique_roles)}")
    logging.info(f"Example rows: {list(unique_roles.values())[:5]}")

    results = list(unique_roles.values())
    results.sort(key=lambda x: x["ai_risk_score"], reverse=True)
    results = results[:100] # Limit to 100 to avoid massive payloads

    # Group vulnerability data by city
    city_risks = {}
    for row in results:
        city = row["city"]
        score = row["ai_risk_score"]
        if city not in city_risks:
            city_risks[city] = []
        city_risks[city].append(score)

    region_scores = {
        city: sum(scores)/len(scores)
        for city, scores in city_risks.items()
    }

    logging.info(f"Returning vulnerability results count: {len(results)}")
    
    return {
        "table": results,
        "regions": region_scores
    }

@router.get("/vulnerability-regions")
def vulnerability_regions():
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

@router.get("/city-role-distribution")
def city_role_distribution(city: str):
    jobs = get_all_jobs()
    city_lower = city.lower()
    counts = Counter()
    for job in jobs:
        candidate_city = str(job.get("city", "")).lower()
        if candidate_city == city_lower:
            role = str(job.get("title", "")).strip()
            if role:
                counts[role] += 1
                
    return [{"name": role, "value": count} for role, count in counts.most_common(10)]

@router.get("/role-city-distribution")
def role_city_distribution(role: str):
    jobs = get_all_jobs()
    role_lower = role.lower()
    counts = Counter()
    for job in jobs:
        candidate_role = str(job.get("title", "")).lower()
        if candidate_role == role_lower:
            city = str(job.get("city", "")).strip()
            if city:
                counts[city] += 1
                
    return [{"name": city, "value": count} for city, count in counts.most_common(10)]
