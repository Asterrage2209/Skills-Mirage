"""
courses_scraper.py
------------------
Orchestrator for SWAYAM + NPTEL course scraping.

Mirrors naukri_scraper.py in structure:
  - run_courses_scraper()  → called on startup / weekly / manual trigger
  - Uses threading.Lock so only one run at a time
  - Writes to data/courses_dataset.py (managed by courses_dataset.py)
  - Saves raw JSON to data/courses_raw.json as backup

Trigger logic (called from main.py):
  - On startup: if dataset is empty → run immediately in background thread
  - Weekly: APScheduler job calls run_courses_scraper() every 7 days
  - Manual: POST /scrape/courses endpoint
"""

import json
import logging
import os
import threading
import time
import uuid
from pathlib import Path

from scrapers.courses.swayam_scraper import scrape_swayam
from scrapers.courses.nptel_scraper import scrape_nptel

logger = logging.getLogger(__name__)

OUTPUT_FILE = Path(__file__).resolve().parents[3] / "data" / "courses_raw.json"

_SCRAPE_LOCK = threading.Lock()


def _normalize_course(course):
    """
    Ensure every course dict has all required fields with correct types.
    This makes dataset_manager ingestion safe regardless of scraper output.
    """
    return {
        "name":           str(course.get("name") or "").strip(),
        "source":         str(course.get("source") or "").strip(),       # SWAYAM / NPTEL
        "domain":         str(course.get("domain") or "").strip(),
        "url":            str(course.get("url") or "").strip(),
        "institution":    str(course.get("institution") or "").strip(),
        "duration_weeks": course.get("duration_weeks"),                  # int or None
        "difficulty":     str(course.get("difficulty") or "").strip(),
        # skill_tags stored as comma-separated string for CSV compatibility
        "skill_tags":     ",".join(course.get("skill_tags") or []),
        # syllabus_weeks stored as JSON string (list of week strings)
        "syllabus_weeks": json.dumps(course.get("syllabus_weeks") or []),
    }


def run_courses_scraper(swayam=True, nptel=True, max_per_source=200):
    """
    Run the full course scrape pipeline.

    Args:
        swayam:         Whether to scrape SWAYAM (default True)
        nptel:          Whether to scrape NPTEL (default True)
        max_per_source: Max courses to scrape per source (default 200)

    Returns:
        dict with stats: total_courses, swayam_count, nptel_count,
                         duration_sec, run_id, output_file
    """
    run_id = uuid.uuid4().hex[:8]
    start_ts = time.time()

    if not _SCRAPE_LOCK.acquire(blocking=False):
        logger.warning("Skipping courses scrape run_id=%s — another run is active", run_id)
        return {
            "total_courses": 0,
            "swayam_count": 0,
            "nptel_count": 0,
            "duration_sec": 0,
            "run_id": run_id,
            "mode": "skipped_busy",
        }

    logger.info("Starting courses scraper run_id=%s", run_id)
    all_courses = []
    swayam_count = 0
    nptel_count = 0

    try:
        if swayam:
            logger.info("Scraping SWAYAM...")
            try:
                swayam_courses = scrape_swayam(max_courses=max_per_source)
                swayam_count = len(swayam_courses)
                all_courses.extend(swayam_courses)
                logger.info("SWAYAM done: %s courses", swayam_count)
            except Exception as e:
                logger.error("SWAYAM scrape failed: %s", e)

        if nptel:
            logger.info("Scraping NPTEL...")
            try:
                nptel_courses = scrape_nptel(max_courses=max_per_source)
                nptel_count = len(nptel_courses)
                all_courses.extend(nptel_courses)
                logger.info("NPTEL done: %s courses", nptel_count)
            except Exception as e:
                logger.error("NPTEL scrape failed: %s", e)

        # Normalize all courses
        normalized = [_normalize_course(c) for c in all_courses if c.get("name")]

        # Save raw JSON backup
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(normalized, f, indent=2)
        logger.info("Wrote %s courses to %s", len(normalized), OUTPUT_FILE)

        # Append to courses dataset (managed store)
        try:
            from data.courses_dataset import append_courses
            append_courses(normalized)
        except Exception as e:
            logger.error("Failed to append to courses dataset: %s", e)

    finally:
        _SCRAPE_LOCK.release()

    stats = {
        "total_courses": len(all_courses),
        "swayam_count": swayam_count,
        "nptel_count": nptel_count,
        "duration_sec": round(time.time() - start_ts, 2),
        "run_id": run_id,
        "output_file": str(OUTPUT_FILE),
    }
    logger.info("Courses scraper stats: %s", stats)
    return stats


def run_courses_scraper_background(max_per_source=200):
    """Run in a daemon thread — used for startup auto-trigger."""
    t = threading.Thread(
        target=run_courses_scraper,
        kwargs={"max_per_source": max_per_source},
        daemon=True,
    )
    t.start()
    logger.info("Courses scraper started in background thread (max_per_source=%s)", max_per_source)
    return t


if __name__ == "__main__":
    run_courses_scraper()