"""
swayam_scraper.py (v2)
----------------------
SWAYAM courses from non-NPTEL national coordinators (CEC, IGNOU, IIMB, UGC, INI, AICTE, NIOS).
NPTEL courses are handled separately by nptel_scraper.py.

Strategy:
  1. Download the official SWAYAM approved course list (public Google Sheet → CSV).
     Jan 2026 semester sheet is linked directly from swayam.gov.in/explorer announcements.
  2. For each course ID, scrape its server-rendered preview page at:
         https://onlinecourses.swayam2.ac.in/{course_id}/preview
     These pages ARE fully server-rendered HTML — BeautifulSoup works perfectly.
     (swayam.gov.in/explorer is a React SPA shell — never scrape that)

Course ID format: {nc_prefix}{YY}_{subject_code}  e.g. cec25_cs01, ini25_cs04
"""

import logging
import re
import time
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Public CSV export of the Jan 2026 SWAYAM approved course list
# Linked from: https://swayam.gov.in/explorer announcements
COURSE_LIST_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vSJ8bOdQOcMPTSADcqznwBr-Em2zzbMGae5e-wKj7SoRuo6CrgF6Csj8n-xfTYyCA"
    "/pub?output=csv"
)

PREVIEW_BASE = "https://onlinecourses.swayam2.ac.in"

# Fallback IDs used when Google Sheet is inaccessible
# Mix of confirmed-working IDs from various coordinators
FALLBACK_COURSE_IDS = [
    # CEC - Computer Science
    "cec25_cs01", "cec25_cs02", "cec25_cs03", "cec25_cs04", "cec25_cs05",
    "cec25_cs06", "cec25_cs07", "cec25_cs08", "cec25_cs09", "cec25_cs10",
    "cec23_cs01",
    # CEC - Management
    "cec25_mg01", "cec25_mg02", "cec25_mg03",
    # INI - CS / Data Science
    "ini25_cs01", "ini25_cs02", "ini25_cs03", "ini25_cs04", "ini25_cs05",
    # INI - Management
    "ini25_mg01", "ini25_mg02", "ini25_mg200", "imb25_mg200",
    # IIMB - Management
    "iimb25_mg01", "iimb25_mg02", "iimb25_mg03",
    # UGC
    "ugc25_hs01", "ugc25_hs02", "ugc25_ss01", "ugc25_ss02",
    # AICTE
    "aicte25_cs01", "aicte25_cs02",
    # NTR (NITTTR)
    "ntr25_ed01", "ntr25_ed02", "ntr25_cs01", "ntr25_ed123",
    # NIOS
    "nos21_sc14",
    # Older stable re-run courses
    "cec21_cs08",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
}
REQUEST_TIMEOUT = 12
DELAY = 0.6


def _get(url):
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp
        except requests.RequestException as e:
            logger.debug("GET attempt %s failed for %s: %s", attempt + 1, url, e)
            time.sleep(1.5)
    return None


def _fetch_course_ids_from_sheet():
    """Download official course list sheet and extract course IDs."""
    resp = _get(COURSE_LIST_CSV_URL)
    if not resp:
        logger.warning("SWAYAM sheet inaccessible — will use fallback IDs.")
        return []

    ids = []
    for line in resp.text.splitlines():
        matches = re.findall(r'swayam2\.ac\.in/([a-z0-9_]+)/preview', line)
        ids.extend(matches)

    # Deduplicate; exclude NPTEL (noc* IDs) — handled by nptel_scraper.py
    ids = list(dict.fromkeys(cid for cid in ids if not cid.startswith("noc")))
    logger.info("SWAYAM sheet: found %s non-NPTEL course IDs", len(ids))
    return ids


def _parse_preview(soup, course_id):
    """Parse a server-rendered /preview page into a course dict."""

    # Name
    h1 = soup.find("h1")
    name = h1.text.strip() if h1 else None

    # Institution — "By Prof. X   |   IIT Kanpur"
    institution = ""
    by_el = soup.find(string=re.compile(r"^\s*By "))
    if by_el:
        parts = str(by_el).split("|")
        if len(parts) >= 2:
            institution = parts[-1].strip()

    # Domain / Category
    domain = ""
    cat_td = soup.find("td", string=re.compile(r"Category", re.I))
    if cat_td:
        val_td = cat_td.find_next_sibling("td")
        if val_td:
            items = [li.text.strip() for li in val_td.find_all("li")]
            domain = items[0] if items else val_td.get_text(strip=True)

    # Duration in weeks
    duration_weeks = None
    dur_td = soup.find("td", string=re.compile(r"Duration", re.I))
    if dur_td:
        val_td = dur_td.find_next_sibling("td")
        if val_td:
            m = re.search(r"(\d+)", val_td.text)
            duration_weeks = int(m.group(1)) if m else None

    # Difficulty / Level
    difficulty = ""
    lvl_td = soup.find("td", string=re.compile(r"^Level", re.I))
    if lvl_td:
        val_td = lvl_td.find_next_sibling("td")
        if val_td:
            difficulty = val_td.get_text(strip=True)

    # Skill tags from Category li items + INTENDED AUDIENCE
    skill_tags = []
    if cat_td:
        val_td = cat_td.find_next_sibling("td")
        if val_td:
            skill_tags = [li.text.strip() for li in val_td.find_all("li") if li.text.strip()]
    full_text = soup.get_text()
    audience = re.search(r"INTENDED AUDIENCE[:\s]+([^\n*]{5,100})", full_text, re.I)
    if audience:
        for word in audience.group(1).split(","):
            tag = word.strip().strip("*").strip()
            if tag and len(tag) < 50 and tag not in skill_tags:
                skill_tags.append(tag)

    # Syllabus — Week N: description
    syllabus = []
    layout = soup.find(lambda t: t.name in ["h3", "h4"] and "course layout" in t.text.lower())
    if layout:
        for tag in layout.find_all_next(["strong", "b"]):
            text = tag.get_text(strip=True)
            if re.match(r"Week\s+\d+", text, re.I):
                syllabus.append(text)
            if len(syllabus) >= 16:
                break
    if not syllabus:
        for m in re.finditer(r"(Week\s+\d+[:\s][^\n]{5,100})", full_text):
            entry = m.group(1).strip()
            if entry not in syllabus:
                syllabus.append(entry)
            if len(syllabus) >= 16:
                break

    return {
        "name": name,
        "source": "SWAYAM",
        "domain": domain,
        "url": f"{PREVIEW_BASE}/{course_id}/preview",
        "institution": institution,
        "duration_weeks": duration_weeks,
        "difficulty": difficulty,
        "skill_tags": skill_tags[:15],
        "syllabus_weeks": syllabus[:16],
    }


def _scrape_one(course_id):
    url = f"{PREVIEW_BASE}/{course_id}/preview"
    resp = _get(url)
    if not resp:
        return None
    soup = BeautifulSoup(resp.text, "lxml")
    h1 = soup.find("h1")
    if not h1 or len(h1.text.strip()) < 3:
        return None
    course = _parse_preview(soup, course_id)
    if course.get("name"):
        logger.debug("SWAYAM scraped: %s", course["name"])
        return course
    return None


def scrape_swayam(max_courses=300):
    """Main entry point. Returns list of course dicts."""
    logger.info("Starting SWAYAM scrape (max=%s)", max_courses)

    ids = _fetch_course_ids_from_sheet()
    if not ids:
        logger.info("Using %s fallback IDs", len(FALLBACK_COURSE_IDS))
        ids = FALLBACK_COURSE_IDS

    courses = []
    for cid in ids[:max_courses]:
        time.sleep(DELAY)
        c = _scrape_one(cid)
        if c:
            courses.append(c)

    logger.info("SWAYAM done: %s courses scraped", len(courses))
    return courses