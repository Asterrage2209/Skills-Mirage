import json
import logging
import os
import queue
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from scrapers.naukri.naukri_parser import extract_job_cards
from scrapers.naukri.naukri_urls import (
    build_city_search_url,
    build_city_search_url_candidates,
    build_search_url,
)
from scrapers.utils.selenium_client import create_driver_pool, fetch_rendered_html
from scrapers.utils.skill_extractor import detect_ai_mentions

ROLES = [
    "data analyst",
    "data scientist",
    "bpo",
    "software engineer",
    "ai engineer",
]

CITIES = ["india"]

MAX_PAGES = 5           # raised: 5 pages × ~20 cards = up to 100 per role pass
SCRAPER_JOB_LIMIT = 150 # target

# 3 parallel drivers is the sweet spot for Naukri:
# fast enough for 150 jobs in ~15 s, low enough to avoid rate-limiting.
DRIVER_POOL_SIZE = 3

OUTPUT_FILE = Path(__file__).resolve().parents[2] / "data" / "raw_jobs.json"
DEBUG_HTML_DIR = Path(__file__).resolve().parents[2] / "data" / "debug_html"

LOG_LEVEL = os.getenv("SCRAPER_LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

BLOCK_HINTS = [
    "captcha", "verify you are human", "access denied",
    "request cannot be processed", "unusual traffic",
    "forbidden", "cloudflare", "akamai", "security check",
]

_SCRAPE_LOCK = threading.Lock()


# ─────────────────────────────────────────────────────────────────────────────
# Driver pool — thread-safe queue
# ─────────────────────────────────────────────────────────────────────────────

class DriverPool:
    """
    Thread-safe pool of Selenium drivers.
    Workers call acquire() to borrow a driver and release() to return it.
    No two threads ever share the same driver instance.
    """
    def __init__(self, drivers):
        self._q = queue.Queue()
        for d in drivers:
            self._q.put(d)

    def acquire(self):
        return self._q.get()          # blocks until one is available

    def release(self, driver):
        self._q.put(driver)

    def quit_all(self):
        while not self._q.empty():
            try:
                self._q.get_nowait().quit()
            except Exception:
                pass


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _looks_blocked(html):
    text = (html or "").lower()
    return any(hint in text for hint in BLOCK_HINTS)


def _matched_block_hints(html):
    text = (html or "").lower()
    return [h for h in BLOCK_HINTS if h in text]


def _save_debug_html(role, city, page, html):
    DEBUG_HTML_DIR.mkdir(parents=True, exist_ok=True)
    name = f"search_{role}_{city}_{page}.html".replace(" ", "_")
    path = DEBUG_HTML_DIR / name
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    logger.info("Saved debug HTML: %s", path)


def _enrich(job, role, city):
    job["ai_mentions"] = detect_ai_mentions(job.get("description") or "")
    job["query_role"] = role
    job["query_city"] = city
    return job


# ─────────────────────────────────────────────────────────────────────────────
# Page fetch tasks (run inside ThreadPoolExecutor workers)
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_city_page(pool, city, page, max_pages, save_debug):
    """
    Fetch one city search page. Borrows a driver, tries URL candidates in
    order, returns the first response that contains job cards.
    """
    driver = pool.acquire()
    candidates = build_city_search_url_candidates(city, page)
    primary_url = candidates[0]
    logger.info("Fetching city page %s/%s: %s", page, max_pages, primary_url)

    html = ""
    cards = []
    used_url = None
    failed = False

    try:
        for url in candidates:
            try:
                # fetch_rendered_html now waits for actual card selectors,
                # not just "body" — so we only get HTML once cards are mounted.
                html = fetch_rendered_html(driver, url)
            except Exception:
                logger.exception("Candidate URL failed: %s", url)
                continue

            cards = extract_job_cards(html)
            if cards:
                used_url = url
                break

        if used_url is None:
            failed = True
            used_url = primary_url
            if save_debug:
                _save_debug_html("all_roles", city, page, html)
            hints = _matched_block_hints(html)
            if hints:
                logger.warning("Possible block city=%s page=%s hints=%s", city, page, hints)

    finally:
        pool.release(driver)

    logger.info(
        "City page result: city=%s page=%s cards=%s url=%s",
        city, page, len(cards), used_url,
    )
    return {"page": page, "cards": cards, "failed": failed, "candidates": candidates, "html": html}


def _fetch_role_page(pool, role, city, page, max_pages, save_debug):
    """Fetch one role search page (used in fallback matrix mode)."""
    driver = pool.acquire()
    url = build_search_url(role, city, page)
    logger.info("Fetching role page %s/%s: %s", page, max_pages, url)

    html = ""
    cards = []
    failed = False

    try:
        try:
            html = fetch_rendered_html(driver, url)
            cards = extract_job_cards(html)
        except Exception:
            logger.exception("Role page fetch failed: %s", url)
            failed = True
            if save_debug:
                _save_debug_html(role, city, page, html)
    finally:
        pool.release(driver)

    logger.info(
        "Role page result: role=%s city=%s page=%s cards=%s",
        role, city, page, len(cards),
    )
    return {"role": role, "city": city, "cards": cards, "failed": failed}


# ─────────────────────────────────────────────────────────────────────────────
# Parallel scrapers
# ─────────────────────────────────────────────────────────────────────────────

def _scrape_city_sequential(pool, city, max_pages, save_debug):
    """
    Submit pages sequentially, enforcing a strict linear crawl:
    page1(1.5s sleep) → page2(1.5s sleep) → page3(1.5s sleep)...
    """
    jobs = []
    failed_pages = 0
    empty_pages = 0

    for page in range(1, max_pages + 1):
        logger.info(f"Scraping page {page} of {max_pages}...")
        
        try:
            result = _fetch_city_page(pool, city, page, max_pages, save_debug)
        except Exception:
            logger.exception("City page fetch raised an exception")
            failed_pages += 1
            time.sleep(1.5)
            continue

        if result["failed"]:
            failed_pages += 1
        
        if not result["cards"]:
            empty_pages += 1
            logger.warning("No cards — tried=%s", result["candidates"])
            # Even if empty, pause before hitting the next page
            time.sleep(1.5)
            continue

        for job in result["cards"]:
            jobs.append(_enrich(job, "all_roles", city))
            
        logger.info(f"Collected {len(jobs)} jobs so far")

        # Always sleep between sequential fetches to avoid blocking
        if page < max_pages:
            time.sleep(1.5)

    logger.info(f"Scraping complete. {len(jobs)} jobs added.")

    return {
        "jobs": jobs,
        "failed_search_pages": failed_pages,
        "failed_job_pages": 0,
        "total_search_pages": max_pages,
        "empty_card_pages": empty_pages,
        "detail_desc_missing": 0,
    }


def _scrape_role_city_matrix_sequential(pool, roles, cities, max_pages, save_debug):
    """
    Fallback: scrape every (role, city, page) combination sequentially.
    """
    jobs = []
    failed_pages = 0
    empty_pages = 0

    tasks = [
        (role, city, page)
        for role in roles
        for city in cities
        for page in range(1, max_pages + 1)
    ]

    for idx, (role, city, page) in enumerate(tasks):
        logger.info(f"Scraping matrix page {page} of {max_pages} (Role: {role}, City: {city})...")

        try:
            result = _fetch_role_page(pool, role, city, page, max_pages, save_debug)
        except Exception:
            logger.exception("Role page fetch raised an exception")
            failed_pages += 1
            time.sleep(1.5)
            continue

        if result["failed"]:
            failed_pages += 1
        
        if not result["cards"]:
            empty_pages += 1

        if result["cards"]:
            for job in result["cards"]:
                jobs.append(_enrich(job, result["role"], result["city"]))
                
        logger.info(f"Collected {len(jobs)} jobs so far")

        # Always sleep between sequential fetches to avoid blocking
        if idx < len(tasks) - 1:
            time.sleep(1.5)

    logger.info(f"Matrix scraping complete. {len(jobs)} jobs added.")

    return {
        "jobs": jobs,
        "failed_search_pages": failed_pages,
        "failed_job_pages": 0,
        "total_search_pages": len(tasks),
        "empty_card_pages": empty_pages,
        "detail_desc_missing": 0,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def run_scraper():
    run_id = uuid.uuid4().hex[:8]
    start_ts = time.time()

    roles = [r.strip() for r in os.getenv("SCRAPER_ROLES", "").split(",") if r.strip()] or ROLES
    cities = [c.strip() for c in os.getenv("SCRAPER_CITIES", "").split(",") if c.strip()] or CITIES
    max_pages = int(os.getenv("SCRAPER_MAX_PAGES", str(MAX_PAGES)))
    scrape_all_roles_for_city = os.getenv("SCRAPER_ALL_ROLES_FOR_CITY", "1") == "1"
    target_city = os.getenv("SCRAPER_TARGET_CITY", "").strip().lower()
    save_debug = os.getenv("SCRAPER_SAVE_DEBUG_HTML", "0") == "1"
    headless = os.getenv("SCRAPER_HEADLESS", "1") != "0"
    pool_size = int(os.getenv("SCRAPER_DRIVER_POOL_SIZE", str(DRIVER_POOL_SIZE)))

    if not _SCRAPE_LOCK.acquire(blocking=False):
        logger.warning("Skipping run_id=%s — another run is active", run_id)
        return {"total_jobs": 0, "mode": "skipped_busy", "run_id": run_id}

    logger.info("Starting Naukri scraper run_id=%s pid=%s", run_id, os.getpid())
    logger.info(
        "Config: roles=%s cities=%s max_pages=%s pool_size=%s headless=%s",
        len(roles), len(cities), max_pages, pool_size, headless,
    )

    if save_debug:
        DEBUG_HTML_DIR.mkdir(parents=True, exist_ok=True)

    raw_drivers = create_driver_pool(size=pool_size, headless=headless)
    driver_pool = DriverPool(raw_drivers)

    jobs = []
    stats = dict(failed_search_pages=0, failed_job_pages=0,
                 total_search_pages=0, empty_card_pages=0, detail_desc_missing=0)

    try:
        if scrape_all_roles_for_city:
            selected_cities = [target_city] if target_city else cities
            if not target_city:
                logger.warning(
                    "SCRAPER_TARGET_CITY not set. Defaulting to '%s'.", selected_cities
                )

            for city in selected_cities:
                logger.info("City-wide scrape: city=%s", city)
                r = _scrape_city_sequential(driver_pool, city, max_pages, save_debug)
                jobs.extend(r["jobs"])
                for k in stats:
                    stats[k] += r.get(k, 0)

            if len(jobs) == 0:
                logger.warning("City-wide scrape returned 0 jobs — falling back to role-city matrix")
                r = _scrape_role_city_matrix_sequential(driver_pool, roles, selected_cities, max_pages, save_debug)
                jobs.extend(r["jobs"])
                for k in stats:
                    stats[k] += r.get(k, 0)
        else:
            r = _scrape_role_city_matrix_sequential(driver_pool, roles, cities, max_pages, save_debug)
            jobs.extend(r["jobs"])
            for k in stats:
                stats[k] += r.get(k, 0)

    finally:
        logger.info("Closing all Chrome drivers")
        driver_pool.quit_all()
        _SCRAPE_LOCK.release()

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2)
    logger.info("Wrote %s jobs to %s", len(jobs), OUTPUT_FILE)

    try:
        from pipeline.job_cleaner import clean_jobs
        from pipeline.skill_extractor import extract_skills
        from data.dataset_manager import append_jobs
        append_jobs(extract_skills(clean_jobs(jobs)))
    except Exception as e:
        logger.error("Pipeline/dataset error: %s", e)

    final_stats = {
        "total_jobs": len(jobs),
        **stats,
        "mode": "all_roles_city" if scrape_all_roles_for_city else "role_city_matrix",
        "target_city": target_city or None,
        "output_file": str(OUTPUT_FILE),
        "run_id": run_id,
        "duration_sec": round(time.time() - start_ts, 2),
    }
    logger.info("Scraper stats: %s", final_stats)
    return final_stats


if __name__ == "__main__":
    run_scraper()