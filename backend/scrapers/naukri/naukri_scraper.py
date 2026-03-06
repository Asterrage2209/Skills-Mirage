import json
import logging
import os
import threading
import time
import uuid
from pathlib import Path

from scrapers.naukri.naukri_parser import extract_job_cards, extract_job_description
from scrapers.naukri.naukri_urls import (
    build_city_search_url,
    build_city_search_url_candidates,
    build_search_url,
)
from scrapers.utils.selenium_client import create_driver, fetch_rendered_html
from scrapers.utils.skill_extractor import detect_ai_mentions

ROLES = [
    "data analyst",
    "data scientist",
    "bpo",
    "software engineer",
    "ai engineer",
]


CITIES = [
    "pune",
    "mumbai",
    "bangalore",
    "delhi",
    "hyderabad",
    "chennai",
    "ahmedabad",
    "indore",
    "jaipur",
    "lucknow",
    "kolkata",
    "noida",
    "gurgaon",
    "coimbatore",
    "kochi",
    "trivandrum",
    "nagpur",
    "bhopal",
    "surat",
    "vadodara",
    "patna",
    "chandigarh",
    "bhubaneswar",
    "visakhapatnam",
    "vijayawada",
    "nashik",
    "mysore",
    "madurai",
    "raipur",
    "dehradun",
]


MAX_PAGES = 4


OUTPUT_FILE = Path(__file__).resolve().parents[2] / "data" / "raw_jobs.json"
DEBUG_HTML_DIR = Path(__file__).resolve().parents[2] / "data" / "debug_html"

LOG_LEVEL = os.getenv("SCRAPER_LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

BLOCK_HINTS = [
    "captcha",
    "verify you are human",
    "access denied",
    "request cannot be processed",
    "unusual traffic",
    "forbidden",
    "cloudflare",
    "akamai",
    "security check",
]


def _looks_blocked(html):
    text = (html or "").lower()
    return any(hint in text for hint in BLOCK_HINTS)


def _matched_block_hints(html):
    text = (html or "").lower()
    return [hint for hint in BLOCK_HINTS if hint in text]


_SCRAPE_LOCK = threading.Lock()


def _scrape_role_city_matrix(driver, roles, cities, max_pages, save_debug_html):
    jobs = []
    failed_search_pages = 0
    failed_job_pages = 0
    total_search_pages = 0
    empty_card_pages = 0
    detail_desc_missing = 0

    for role in roles:
        for city in cities:
            logger.info("Processing query role=%s city=%s", role, city)
            for page in range(1, max_pages + 1):
                total_search_pages += 1
                url = build_search_url(role, city, page)
                logger.info("Fetching search page %s/%s: %s", page, max_pages, url)

                try:
                    html = fetch_rendered_html(driver, url, wait_selector="body")
                except Exception:
                    failed_search_pages += 1
                    logger.exception("Failed search page: %s", url)
                    continue

                cards = extract_job_cards(html)
                logger.info(
                    "Search result parsed: role=%s city=%s page=%s cards=%s",
                    role,
                    city,
                    page,
                    len(cards),
                )
                if not cards:
                    empty_card_pages += 1
                    logger.warning("No cards found for URL: %s", url)
                    logger.debug("Search page title: %s", driver.title)
                    if _looks_blocked(html):
                        logger.warning("Possible anti-bot/block page detected for URL: %s", url)
                    logger.debug("Search page HTML preview: %s", html[:500].replace("\n", " "))
                    if save_debug_html:
                        snapshot = DEBUG_HTML_DIR / f"search_{role}_{city}_{page}.html"
                        snapshot_name = snapshot.name.replace(" ", "_")
                        snapshot = snapshot.with_name(snapshot_name)
                        with open(snapshot, "w", encoding="utf-8") as f:
                            f.write(html)
                        logger.info("Saved debug search HTML: %s", snapshot)

                for job in cards:
                    if job["job_url"]:
                        try:
                            detail_html = fetch_rendered_html(
                                driver, job["job_url"], wait_selector="body", timeout=8
                            )
                            description = extract_job_description(detail_html)
                            if description:
                                job["description"] = description
                            else:
                                detail_desc_missing += 1
                                logger.debug("No detail description parsed for job URL: %s", job["job_url"])
                        except Exception:
                            failed_job_pages += 1
                            logger.exception("Failed job page: %s", job["job_url"])

                    job["ai_mentions"] = detect_ai_mentions(job.get("description") or "")
                    job["query_role"] = role
                    job["query_city"] = city
                    jobs.append(job)
                logger.info("Accumulated jobs so far: %s", len(jobs))

    return {
        "jobs": jobs,
        "failed_search_pages": failed_search_pages,
        "failed_job_pages": failed_job_pages,
        "total_search_pages": total_search_pages,
        "empty_card_pages": empty_card_pages,
        "detail_desc_missing": detail_desc_missing,
    }


def run_scraper():
    run_id = uuid.uuid4().hex[:8]
    start_ts = time.time()
    roles = ROLES
    cities = CITIES
    max_pages = MAX_PAGES
    if os.getenv("SCRAPER_ROLES"):
        roles = [r.strip() for r in os.getenv("SCRAPER_ROLES", "").split(",") if r.strip()]
    if os.getenv("SCRAPER_CITIES"):
        cities = [c.strip() for c in os.getenv("SCRAPER_CITIES", "").split(",") if c.strip()]
    if os.getenv("SCRAPER_MAX_PAGES"):
        max_pages = int(os.getenv("SCRAPER_MAX_PAGES", "1"))
    scrape_all_roles_for_city = os.getenv("SCRAPER_ALL_ROLES_FOR_CITY", "1") == "1"
    target_city = os.getenv("SCRAPER_TARGET_CITY", "").strip().lower()

    if not _SCRAPE_LOCK.acquire(blocking=False):
        logger.warning("Skipping scraper run_id=%s because another run is already active", run_id)
        return {
            "total_jobs": 0,
            "total_search_pages": 0,
            "failed_search_pages": 0,
            "failed_job_pages": 0,
            "empty_card_pages": 0,
            "detail_desc_missing": 0,
            "mode": "skipped_busy",
            "target_city": target_city or None,
            "output_file": str(OUTPUT_FILE),
            "run_id": run_id,
        }

    logger.info("Starting Naukri scraper run_id=%s pid=%s", run_id, os.getpid())
    logger.info(
        "Config run_id=%s: roles=%s cities=%s max_pages=%s all_roles_for_city=%s target_city=%s",
        run_id,
        len(roles),
        len(cities),
        max_pages,
        scrape_all_roles_for_city,
        target_city or "none",
    )
    jobs = []
    failed_search_pages = 0
    failed_job_pages = 0
    total_search_pages = 0
    empty_card_pages = 0
    detail_desc_missing = 0

    save_debug_html = os.getenv("SCRAPER_SAVE_DEBUG_HTML", "0") == "1"
    if save_debug_html:
        DEBUG_HTML_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("Debug HTML saving is enabled at %s", DEBUG_HTML_DIR)

    headless = os.getenv("SCRAPER_HEADLESS", "1") != "0"
    logger.info("Browser mode: headless=%s", headless)
    driver = create_driver(headless=headless)

    try:
        if scrape_all_roles_for_city:
            if target_city:
                selected_cities = [target_city]
            else:
                selected_cities = cities
                logger.warning(
                    "SCRAPER_TARGET_CITY not set. Defaulting city-wide scrape to '%s'.",
                    selected_cities,
                )
            for city in selected_cities:
                role = "all_roles"
                logger.info("Processing city-wide query city=%s", city)
                for page in range(1, max_pages + 1):
                    total_search_pages += 1
                    primary_url = build_city_search_url(city, page)
                    candidates = build_city_search_url_candidates(city, page)
                    logger.info("Fetching city search page %s/%s: %s", page, max_pages, primary_url)

                    html = ""
                    cards = []
                    used_url = None

                    for candidate_url in candidates:
                        try:
                            html = fetch_rendered_html(driver, candidate_url, wait_selector="body")
                        except Exception:
                            logger.exception("Failed city candidate URL: %s", candidate_url)
                            continue

                        candidate_cards = extract_job_cards(html)
                        if candidate_cards:
                            cards = candidate_cards
                            used_url = candidate_url
                            break

                    if used_url is None:
                        failed_search_pages += 1
                        used_url = primary_url

                    logger.info(
                        "Search result parsed: role=%s city=%s page=%s cards=%s url=%s",
                        role,
                        city,
                        page,
                        len(cards),
                        used_url,
                    )
                    if not cards:
                        empty_card_pages += 1
                        logger.warning("No cards found for city page. tried=%s", candidates)
                        logger.debug("Search page title: %s", driver.title)
                        matches = _matched_block_hints(html)
                        if matches:
                            logger.warning(
                                "Possible anti-bot/block page detected for city=%s page=%s matched_hints=%s",
                                city,
                                page,
                                matches,
                            )
                        logger.debug("Search page HTML preview: %s", html[:500].replace("\n", " "))
                        if save_debug_html:
                            snapshot = DEBUG_HTML_DIR / f"search_{role}_{city}_{page}.html"
                            snapshot_name = snapshot.name.replace(" ", "_")
                            snapshot = snapshot.with_name(snapshot_name)
                            with open(snapshot, "w", encoding="utf-8") as f:
                                f.write(html)
                            logger.info("Saved debug search HTML: %s", snapshot)

                    for job in cards:
                        if job["job_url"]:
                            try:
                                detail_html = fetch_rendered_html(
                                    driver, job["job_url"], wait_selector="body", timeout=8
                                )
                                description = extract_job_description(detail_html)
                                if description:
                                    job["description"] = description
                                else:
                                    detail_desc_missing += 1
                                    logger.debug("No detail description parsed for job URL: %s", job["job_url"])
                            except Exception as exc:
                                failed_job_pages += 1
                                logger.exception("Failed job page: %s", job["job_url"])

                        job["ai_mentions"] = detect_ai_mentions(job.get("description") or "")
                        job["query_role"] = role
                        job["query_city"] = city
                        jobs.append(job)
                    logger.info("Accumulated jobs so far: %s", len(jobs))

            if len(jobs) == 0:
                logger.warning(
                    "City-wide scrape returned 0 jobs. Falling back to role-city matrix for cities=%s",
                    selected_cities,
                )
                fallback = _scrape_role_city_matrix(driver, roles, selected_cities, max_pages, save_debug_html)
                jobs.extend(fallback["jobs"])
                failed_search_pages += fallback["failed_search_pages"]
                failed_job_pages += fallback["failed_job_pages"]
                total_search_pages += fallback["total_search_pages"]
                empty_card_pages += fallback["empty_card_pages"]
                detail_desc_missing += fallback["detail_desc_missing"]
        else:
            result = _scrape_role_city_matrix(driver, roles, cities, max_pages, save_debug_html)
            jobs.extend(result["jobs"])
            failed_search_pages += result["failed_search_pages"]
            failed_job_pages += result["failed_job_pages"]
            total_search_pages += result["total_search_pages"]
            empty_card_pages += result["empty_card_pages"]
            detail_desc_missing += result["detail_desc_missing"]
    finally:
        logger.info("Closing Chrome driver")
        try:
            driver.quit()
        except Exception:
            logger.debug("Driver was already closed")
        _SCRAPE_LOCK.release()

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2)
    logger.info("Wrote output file: %s", OUTPUT_FILE)

    try:
        from pipeline.job_cleaner import clean_jobs
        from pipeline.skill_extractor import extract_skills
        from data.dataset_manager import append_jobs

        cleaned_jobs = clean_jobs(jobs)
        skilled_jobs = extract_skills(cleaned_jobs)
        append_jobs(skilled_jobs)
    except Exception as e:
        logger.error("Failed to append to dataset: %s", e)

    stats = {
        "total_jobs": len(jobs),
        "total_search_pages": total_search_pages,
        "failed_search_pages": failed_search_pages,
        "failed_job_pages": failed_job_pages,
        "empty_card_pages": empty_card_pages,
        "detail_desc_missing": detail_desc_missing,
        "mode": "all_roles_city" if scrape_all_roles_for_city else "role_city_matrix",
        "target_city": target_city or None,
        "output_file": str(OUTPUT_FILE),
        "run_id": run_id,
        "duration_sec": round(time.time() - start_ts, 2),
    }
    logger.info("Scraper stats: %s", stats)
    return stats


if __name__ == "__main__":
    run_scraper()
