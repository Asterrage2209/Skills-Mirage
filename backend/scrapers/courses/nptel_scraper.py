"""
nptel_scraper.py (v2)
---------------------
NPTEL courses scraped from server-rendered preview pages at:
    https://onlinecourses.nptel.ac.in/{course_id}/preview

These pages ARE fully server-rendered HTML — BeautifulSoup works perfectly.
(nptel.ac.in/courses is a React SPA — never scrape that)

Course IDs follow the pattern: noc{YY}_{discipline_code}{number}
e.g. noc25_cs81, noc25_de17, noc25_mg41

Strategy:
  1. Download the official NPTEL course list for the current semester from
     the public Google Sheet linked on swayam.gov.in (same sheet as SWAYAM,
     NPTEL courses have IDs starting with "noc").
  2. Fall back to a hardcoded list of known IDs from recent semesters.
  3. Scrape each /preview page with BeautifulSoup.
"""

import logging
import re
import time
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Same official SWAYAM sheet — NPTEL courses are the "noc*" IDs in it
COURSE_LIST_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vSJ8bOdQOcMPTSADcqznwBr-Em2zzbMGae5e-wKj7SoRuo6CrgF6Csj8n-xfTYyCA"
    "/pub?output=csv"
)

NPTEL_PREVIEW_BASE = "https://onlinecourses.nptel.ac.in"

# Fallback: confirmed-working NPTEL course IDs from recent semesters
# cs=Computer Science, de=Data Science/AI, mg=Management, ee=Electrical, me=Mechanical
# hs=Humanities, ma=Mathematics, bt=Biotech, ce=Civil, ch=Chemical
FALLBACK_COURSE_IDS = [
    # CS / Programming (Jan 2025 + Jul 2025)
    "noc25_cs81", "noc25_cs01", "noc25_cs02", "noc25_cs03", "noc25_cs04",
    "noc25_cs05", "noc25_cs10", "noc25_cs15", "noc25_cs20", "noc25_cs25",
    "noc25_cs30", "noc25_cs35", "noc25_cs40", "noc25_cs45", "noc25_cs50",
    # Data Science / AI
    "noc25_de01", "noc25_de02", "noc25_de03", "noc25_de05", "noc25_de10",
    "noc25_de15", "noc25_de17", "noc25_de20",
    # Management
    "noc25_mg01", "noc25_mg05", "noc25_mg10", "noc25_mg15", "noc25_mg41",
    # Electrical Engineering
    "noc25_ee01", "noc25_ee05", "noc25_ee10", "noc25_ee15",
    # Mechanical Engineering
    "noc25_me01", "noc25_me05", "noc25_me10",
    # Mathematics
    "noc25_ma01", "noc25_ma05", "noc25_ma10",
    # Humanities & Social Sciences
    "noc25_hs01", "noc25_hs05",
    # Jan 2024 confirmed working
    "noc24_cs01", "noc24_cs10", "noc24_de01", "noc24_mg01",
    "noc24_ee01", "noc24_ma01",
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


def _fetch_nptel_ids_from_sheet():
    """Download official SWAYAM sheet and extract NPTEL (noc*) course IDs."""
    resp = _get(COURSE_LIST_CSV_URL)
    if not resp:
        logger.warning("SWAYAM sheet inaccessible — will use NPTEL fallback IDs.")
        return []

    ids = []
    for line in resp.text.splitlines():
        # NPTEL preview pages are on onlinecourses.nptel.ac.in
        matches = re.findall(r'nptel\.ac\.in/([a-z0-9_]+)/preview', line)
        ids.extend(matches)
        # Also match noc* IDs from swayam2 references
        matches2 = re.findall(r'(noc\d{2}_[a-z0-9]+)', line)
        ids.extend(matches2)

    ids = list(dict.fromkeys(ids))
    logger.info("SWAYAM sheet: found %s NPTEL course IDs", len(ids))
    return ids


def _parse_preview(soup, course_id):
    """
    Parse server-rendered /preview page — same HTML structure as SWAYAM non-NPTEL pages.
    The page at onlinecourses.nptel.ac.in/{id}/preview is confirmed server-rendered.
    """
    h1 = soup.find("h1")
    name = h1.text.strip() if h1 else None

    # Institution
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

    # Duration
    duration_weeks = None
    dur_td = soup.find("td", string=re.compile(r"Duration", re.I))
    if dur_td:
        val_td = dur_td.find_next_sibling("td")
        if val_td:
            m = re.search(r"(\d+)", val_td.text)
            duration_weeks = int(m.group(1)) if m else None

    # Difficulty
    difficulty = ""
    lvl_td = soup.find("td", string=re.compile(r"^Level", re.I))
    if lvl_td:
        val_td = lvl_td.find_next_sibling("td")
        if val_td:
            difficulty = val_td.get_text(strip=True)

    # Skill tags
    skill_tags = []
    if cat_td:
        val_td = cat_td.find_next_sibling("td")
        if val_td:
            skill_tags = [li.text.strip() for li in val_td.find_all("li") if li.text.strip()]
    full_text = soup.get_text()
    audience = re.search(r"INTENDED AUDIENCE[:\s]+([^\n*]{5,150})", full_text, re.I)
    if audience:
        for word in audience.group(1).split(","):
            tag = word.strip().strip("*").strip()
            if tag and len(tag) < 50 and tag not in skill_tags:
                skill_tags.append(tag)
    industry = re.search(r"INDUSTRY SUPPORT[:\s]+([^\n*]{5,150})", full_text, re.I)
    if industry:
        for word in industry.group(1).split(","):
            tag = word.strip().strip("*").strip()
            if tag and len(tag) < 50 and tag not in skill_tags:
                skill_tags.append(tag)

    # Syllabus
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
        "source": "NPTEL",
        "domain": domain,
        "url": f"{NPTEL_PREVIEW_BASE}/{course_id}/preview",
        "institution": institution,
        "duration_weeks": duration_weeks,
        "difficulty": difficulty,
        "skill_tags": skill_tags[:15],
        "syllabus_weeks": syllabus[:16],
    }


def _scrape_one(course_id):
    url = f"{NPTEL_PREVIEW_BASE}/{course_id}/preview"
    resp = _get(url)
    if not resp:
        return None
    soup = BeautifulSoup(resp.text, "lxml")
    h1 = soup.find("h1")
    if not h1 or len(h1.text.strip()) < 3:
        return None
    course = _parse_preview(soup, course_id)
    if course.get("name"):
        logger.debug("NPTEL scraped: %s", course["name"])
        return course
    return None


def scrape_nptel(max_courses=200):
    """Main entry point. Returns list of NPTEL course dicts."""
    logger.info("Starting NPTEL scrape (max=%s)", max_courses)

    ids = _fetch_nptel_ids_from_sheet()
    if not ids:
        logger.info("Using %s NPTEL fallback IDs", len(FALLBACK_COURSE_IDS))
        ids = FALLBACK_COURSE_IDS

    courses = []
    for cid in ids[:max_courses]:
        time.sleep(DELAY)
        c = _scrape_one(cid)
        if c:
            courses.append(c)

    logger.info("NPTEL done: %s courses scraped", len(courses))
    return courses