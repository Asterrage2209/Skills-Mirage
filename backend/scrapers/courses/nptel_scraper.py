"""
nptel_scraper.py (v3)
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
  4. Extract ACTIONABLE skill tags (like naukri_jobs format) not discipline codes.
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
    "/pub?output=csv&gid=3134725"            # NPTEL_ tab
)

NPTEL_PREVIEW_BASE = "https://onlinecourses.nptel.ac.in"

# Fallback: confirmed-working NPTEL course IDs from recent semesters
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

# ─── Discipline / noise terms to REMOVE from skill tags ──────────────────────
# These are department names, degree types, generic phrases — NOT actionable skills
_NOISE_PATTERNS = {
    # Broad discipline names (the main offenders)
    "computer science and engineering", "computer science & engineering",
    "computer science", "electrical engineering",
    "electronics and communications engineering",
    "electrical, electronics and communications engineering",
    "mechanical engineering", "civil engineering", "chemical engineering",
    "design engineering", "management studies", "mathematics",
    "humanities and social sciences", "humanities & social sciences",
    "architecture and planning", "multidisciplinary", "biotechnology",
    "aerospace engineering", "metallurgical and materials engineering",
    "textile engineering", "mining engineering", "ocean engineering",
    "physics", "chemistry", "biosciences", "bioengineering",
    "water resources engineering", "agricultural engineering",
    "environmental science",
    # Abbreviations for departments
    "cse", "ece", "eee", "ee", "me", "ce", "it",
    # Degree / audience noise
    "undergraduate", "postgraduate", "ug", "pg",
    "b.tech", "m.tech", "b.sc", "m.sc", "ph.d", "phd",
    "btech", "mtech", "mba", "bba", "b.com", "m.com",
    "students", "faculty", "open for all", "open to all",
    "engineering students", "engineering colleges",
    "ug and pg students", "ug or pg",
    # Company noise patterns
    "in general", "etc.", "etc",
    # Generic
    "information technology",
}

# Additional patterns matched by regex (can't be in the set)
_NOISE_DEGREE_PATTERNS = re.compile(
    r'^(b\.?b\.?a|b\.?com|m\.?com|b\.?sc|m\.?sc|b\.?a|m\.?a|b\.?tech|m\.?tech|'
    r'phd|mba|bba|b\.?e|m\.?e)'
    r'(\s|\.|\(|$)', re.I
)

# Minimum tag length to keep
_MIN_TAG_LEN = 3
_MAX_TAG_LEN = 60


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
    """Download the NPTEL tab of the official SWAYAM sheet and extract course IDs."""
    resp = _get(COURSE_LIST_CSV_URL)
    if not resp:
        logger.warning("SWAYAM sheet inaccessible — will use NPTEL fallback IDs.")
        return []

    ids = []
    for line in resp.text.splitlines():
        # Match preview URLs like nptel.ac.in/noc25_cs81/preview
        matches = re.findall(r'nptel\.ac\.in/([a-z0-9_]+)/preview', line)
        ids.extend(matches)
        # Also match noc* IDs from swayam2 references
        matches2 = re.findall(r'(noc\d{2}_[a-z0-9]+)', line)
        ids.extend(matches2)

    ids = list(dict.fromkeys(ids))
    logger.info("NPTEL sheet tab: found %s course IDs", len(ids))
    return ids


def _is_noise(tag):
    """Return True if the tag is a discipline, degree type, or generic noise."""
    tag_lower = tag.lower().strip()
    if len(tag_lower) < _MIN_TAG_LEN or len(tag_lower) > _MAX_TAG_LEN:
        return True
    if tag_lower in _NOISE_PATTERNS:
        return True
    # Skip if it looks like a truncated entry (ends mid-word or with single char)
    if re.search(r'\s[a-z]$', tag_lower):  # ends with " x" (single char)
        return True
    # Skip sentence-like phrases (contain common verbs/articles that real skills don't)
    sentence_markers = [
        " would ", " should ", " could ", " will ", " this ", " that ",
        " value ", " find ", " useful", " desirable", " required",
        " not essential", " but not", " although",
        "students of ", "students in ", " students",
        "ug and pg", "ug or pg", "undergraduate",
        " who ", " are ", " is ", " was ", " has ", " have ",
    ]
    for marker in sentence_markers:
        if marker in tag_lower:
            return True
    # Skip INDUSTRY SUPPORT / PREREQUISITES header text leaking in
    if "industry support" in tag_lower or "prerequisites" in tag_lower:
        return True
    if "intended audience" in tag_lower:
        return True
    # Skip if it's just a degree/role descriptor
    if re.match(r'^(b\.?tech|m\.?tech|b\.?sc|m\.?sc|phd|mba|bba)\b', tag_lower):
        return True
    # Skip entries that look like tab-separated text (broken CSV)
    if '\t' in tag_lower:
        return True
    # Skip too-generic single words that aren't skills
    generic_words = {
        "e.g", "e.g.", "i.e", "i.e.", "and", "or", "the", "for", "with",
        "any", "all", "also", "based", "basic", "level", "course",
        "module", "introduction", "various", "related",
    }
    if tag_lower in generic_words:
        return True
    # Skip fragments starting with 'and ' (broken comma splits)
    if tag_lower.startswith("and ") or tag_lower.startswith("or "):
        return True
    # Skip if contains parentheses (usually long industry text)
    if '(' in tag_lower and len(tag_lower) > 30:
        return True
    # Skip 'exposure to ...' type phrases
    if tag_lower.startswith("exposure to "):
        return True
    # Skip entries ending with 'etc.)' or containing 'etc'
    if tag_lower.endswith("etc.") or tag_lower.endswith("etc.)") or tag_lower == "etc":
        return True
    # Skip degree/program names like B.B.A, B.Com. (Honours), M.Sc etc.
    if _NOISE_DEGREE_PATTERNS.match(tag_lower):
        return True
    # Skip URL fragments
    if re.match(r'^(https?://|www\.|[a-z]+\.ac\.|[a-z]+\.com)', tag_lower):
        return True
    return False


def _extract_skills_from_name(course_name):
    """
    Extract skill-like keywords from the course title.
    e.g. "Data Structures and Algorithms Design" →
         ["Data Structures", "Algorithms", "Algorithm Design"]
    """
    if not course_name:
        return []

    skills = []
    name = course_name.strip()

    # The full course name is itself a skill topic
    if len(name) > 3 and not _is_noise(name):
        skills.append(name)

    return skills


def _extract_skills_from_text(text, label=""):
    """
    Extract comma-separated skill terms from a text block.
    Filters out noise/discipline terms.
    """
    if not text:
        return []

    skills = []
    # Split on commas and common delimiters
    for part in re.split(r'[,;/]', text):
        tag = part.strip().strip("*").strip(".")
        # Clean up PREREQUISITES / INDUSTRY SUPPORT prefix text
        tag = re.sub(r'^(PREREQUISITES\s*:\s*|INDUSTRY SUPPORT\s*:\s*)', '', tag, flags=re.I)
        tag = tag.strip()
        if tag and not _is_noise(tag):
            skills.append(tag)

    return skills


def _clean_skill_tags(raw_tags):
    """
    Deduplicate, filter noise, and normalize skill tags.
    Returns a clean list of actionable skill strings.
    """
    seen = set()
    clean = []
    for tag in raw_tags:
        tag = tag.strip()
        if not tag or _is_noise(tag):
            continue
        # Normalize for dedup
        key = tag.lower().strip()
        if key not in seen:
            seen.add(key)
            clean.append(tag)
    return clean


def _parse_preview(soup, course_id):
    """
    Parse server-rendered /preview page.
    Extract actual actionable skill tags, not discipline codes.
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

    # Domain / Category — keep this as domain, NOT as skill tags
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

    # ─── Skill Tags (the FIX) ────────────────────────────────────────────────
    # Instead of copying Category <li> items (discipline codes),
    # we extract actual skills from:
    #   1. Course name (e.g. "Data Structures and Algorithms Design")
    #   2. INTENDED AUDIENCE section (has useful sub-topics)
    #   3. INDUSTRY SUPPORT section (has company/sector names = skills context)
    #   4. PREREQUISITES section (tells you what skills are involved)
    #   5. Category sub-items after the first (first is always the discipline)
    skill_tags = []

    # 1. Course name → primary skill
    skill_tags.extend(_extract_skills_from_name(name))

    # 2. Category sub-items (skip first — it's the discipline name that goes to domain)
    if cat_td:
        val_td = cat_td.find_next_sibling("td")
        if val_td:
            cat_items = [li.text.strip() for li in val_td.find_all("li") if li.text.strip()]
            # Skip the first item (discipline like "Computer Science and Engineering")
            for item in cat_items[1:]:
                skill_tags.extend(_extract_skills_from_text(item))

    # 3. Parse full text for INTENDED AUDIENCE, INDUSTRY SUPPORT, PREREQUISITES
    full_text = soup.get_text()

    audience = re.search(r"INTENDED AUDIENCE[:\s]+([^\n*]{5,200})", full_text, re.I)
    if audience:
        skill_tags.extend(_extract_skills_from_text(audience.group(1)))

    industry = re.search(r"INDUSTRY SUPPORT[:\s]+([^\n*]{5,200})", full_text, re.I)
    if industry:
        skill_tags.extend(_extract_skills_from_text(industry.group(1)))

    prereqs = re.search(r"PREREQUISITES[:\s]+([^\n*]{5,200})", full_text, re.I)
    if prereqs:
        skill_tags.extend(_extract_skills_from_text(prereqs.group(1)))

    # Clean and deduplicate
    skill_tags = _clean_skill_tags(skill_tags)

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
        logger.debug("NPTEL scraped: %s → skills=%s", course["name"], course["skill_tags"][:5])
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