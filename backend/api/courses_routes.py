"""
courses_routes.py
-----------------
FastAPI router for course-related endpoints.

Endpoints:
  GET  /courses              → all courses (paginated)
  GET  /courses/stats        → dataset stats (total, by source, domains)
  GET  /courses/for-skills   → courses matching a list of skills (Tab B gap map)
  GET  /courses/reskilling   → courses for a reskilling path (Layer 2)
  POST /scrape/courses       → manually trigger a fresh scrape
"""

import logging
from typing import Optional
from fastapi import APIRouter, Query, BackgroundTasks

from data.courses_dataset import (
    get_all_courses,
    get_stats,
    query_courses_for_skills,
    query_courses_for_reskilling,
    get_courses_by_source,
)
from scrapers.courses.courses_scraper import run_courses_scraper

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/courses")
def list_courses(
    source: Optional[str] = Query(None, description="Filter by source: SWAYAM or NPTEL"),
    domain: Optional[str] = Query(None, description="Filter by domain/discipline"),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
):
    """
    Return all courses, optionally filtered by source or domain.
    Paginated via limit/offset.
    """
    if source:
        courses = get_courses_by_source(source)
    else:
        courses = get_all_courses()

    if domain:
        domain_lower = domain.lower()
        courses = [c for c in courses if domain_lower in c.get("domain", "").lower()]

    total = len(courses)
    page = courses[offset: offset + limit]

    return {"total": total, "offset": offset, "limit": limit, "courses": page}


@router.get("/courses/stats")
def courses_stats():
    """
    Dataset statistics — used on dashboard to show data freshness.
    Returns total count, breakdown by source, and list of domains.
    """
    return get_stats()


@router.get("/courses/for-skills")
def courses_for_skills(
    skills: str = Query(..., description="Comma-separated skill names, e.g. Python,ML,SQL"),
    max_results: int = Query(20, le=50),
):
    """
    Layer 1 Tab B — skill gap map.
    Given a list of in-demand skills (from job postings),
    return courses that teach those skills.

    Used to answer: "What's being hired vs what's being trained?"
    """
    skill_list = [s.strip() for s in skills.split(",") if s.strip()]
    if not skill_list:
        return {"courses": [], "skills_queried": []}

    results = query_courses_for_skills(skill_list, max_results=max_results)
    return {"courses": results, "skills_queried": skill_list}


@router.get("/courses/reskilling")
def courses_for_reskilling(
    target_role: str = Query(..., description="Target job role, e.g. 'Data Analyst'"),
    current_skills: Optional[str] = Query(None, description="Comma-separated current skills"),
    max_weeks: Optional[int] = Query(None, description="Max course duration in weeks"),
    max_results: int = Query(10, le=30),
):
    """
    Layer 2 — reskilling path builder.
    Returns ordered list of courses relevant to transitioning
    into target_role, filtered by max_weeks if provided.

    Called by reskilling_engine.py to build the week-by-week path.
    """
    skills = [s.strip() for s in (current_skills or "").split(",") if s.strip()]
    results = query_courses_for_reskilling(
        target_role=target_role,
        current_skills=skills,
        max_weeks=max_weeks,
        max_results=max_results,
    )
    return {
        "target_role": target_role,
        "max_weeks": max_weeks,
        "courses": results,
    }


@router.post("/scrape/courses")
def trigger_courses_scrape(
    background_tasks: BackgroundTasks,
    swayam: bool = Query(True, description="Scrape SWAYAM"),
    nptel: bool = Query(True, description="Scrape NPTEL"),
):
    """
    Manually trigger a fresh course scrape in the background.
    Returns immediately — check /courses/stats for updated counts.
    """
    logger.info("Manual course scrape triggered via API swayam=%s nptel=%s", swayam, nptel)
    background_tasks.add_task(run_courses_scraper, swayam=swayam, nptel=nptel)
    return {
        "status": "started",
        "message": "Course scrape running in background. Check /courses/stats for progress.",
        "sources": {"swayam": swayam, "nptel": nptel},
    }