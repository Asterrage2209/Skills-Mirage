"""
swayam_scraper.py (v4)
----------------------
SWAYAM courses from non-NPTEL national coordinators:
  CEC, IIMB, NITTTR, AICTE, INI, UGC, IGNOU

Strategy:
  Since swayam2.ac.in uses a Next.js SPA (no server-rendered HTML),
  we extract ALL course data directly from the Google Sheet CSV tabs.
  Each tab contains rich metadata:
    - Course Title, Discipline, Coordinator, Start/End dates
    - Host University, Level, NCrF, Duration, Credits
    - Industry Aligned, Industry Sectors, Language, Preview URL

  This gives us 700+ courses without needing to hit the SPA at all.
"""

import csv
import io
import logging
import re
import time
import requests

logger = logging.getLogger(__name__)

# ─── Google Sheet tab GIDs (each coordinator has its own tab) ────────────────
SHEET_BASE = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vSJ8bOdQOcMPTSADcqznwBr-Em2zzbMGae5e-wKj7SoRuo6CrgF6Csj8n-xfTYyCA"
    "/pub?output=csv&gid="
)

# Coordinator → Sheet tab GID
COORDINATOR_TABS = {
    "CEC":    "2033916737",
    "IIMB":   "614727677",
    "NITTTR": "1431459972",
    "AICTE":  "36327938",
    "INI":    "1605318222",
    "UGC":    "986949470",
    "IGNOU":  "1291455978",
}

PREVIEW_BASE = "https://onlinecourses.swayam2.ac.in"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
}
REQUEST_TIMEOUT = 15

# ─── Noise filter ────────────────────────────────────────────────────────────
_NOISE_PATTERNS = {
    "computer science and engineering", "computer science & engineering",
    "computer science", "electrical engineering",
    "electronics and communications engineering",
    "mechanical engineering", "civil engineering", "chemical engineering",
    "design engineering", "management studies", "mathematics",
    "humanities and social sciences", "humanities & social sciences",
    "architecture and planning", "multidisciplinary", "biotechnology",
    "aerospace engineering", "metallurgical and materials engineering",
    "textile engineering", "mining engineering", "ocean engineering",
    "physics", "chemistry", "biosciences", "bioengineering",
    "environmental science", "information technology",
    "generic elective", "foundation course", "community science",
    # Abbreviations
    "cse", "ece", "eee", "ee", "me", "ce", "it",
    # Degree / audience noise
    "undergraduate", "postgraduate", "ug", "pg",
    "b.tech", "m.tech", "b.sc", "m.sc", "ph.d", "phd",
    "btech", "mtech", "mba", "bba", "b.com", "m.com",
    "b.a", "m.a", "ba", "ma", "b.a.", "m.a.",
    "b.sc.", "m.sc.", "ba hons", "ba hons.",
    "students", "faculty", "open for all", "open to all",
    "engineering students", "engineering colleges",
    "in general", "etc.", "etc", "na", "no",
    "yes", "teaching", "cop",
}

# Degree/program patterns matched by regex
_NOISE_DEGREE_PATTERNS = re.compile(
    r'^(b\.?b\.?a|b\.?com|m\.?com|b\.?sc|m\.?sc|b\.?a|m\.?a|b\.?tech|m\.?tech|'
    r'phd|mba|bba|b\.?e|m\.?e)'
    r'(\s|\.|\(|$)', re.I
)

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


def _is_noise(tag):
    """Return True if the tag is a discipline, degree, or noise term."""
    tag_lower = tag.lower().strip()
    if len(tag_lower) < _MIN_TAG_LEN or len(tag_lower) > _MAX_TAG_LEN:
        return True
    if tag_lower in _NOISE_PATTERNS:
        return True
    if re.search(r'\s[a-z]$', tag_lower):
        return True
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
    if "industry support" in tag_lower or "prerequisites" in tag_lower:
        return True
    if "intended audience" in tag_lower:
        return True
    if re.match(r'^(b\.?tech|m\.?tech|b\.?sc|m\.?sc|phd|mba|bba)\b', tag_lower):
        return True
    if '\t' in tag_lower:
        return True
    generic_words = {
        "e.g", "e.g.", "i.e", "i.e.", "and", "or", "the", "for", "with",
        "any", "all", "also", "based", "basic", "level", "course",
        "module", "introduction", "various", "related",
    }
    if tag_lower in generic_words:
        return True
    if tag_lower.startswith("and ") or tag_lower.startswith("or "):
        return True
    if '(' in tag_lower and len(tag_lower) > 30:
        return True
    if tag_lower.startswith("exposure to "):
        return True
    if tag_lower.endswith("etc.") or tag_lower.endswith("etc.)") or tag_lower == "etc":
        return True
    # Skip degree/program names like B.B.A, B.Com. (Honours)
    if _NOISE_DEGREE_PATTERNS.match(tag_lower):
        return True
    # Skip URL fragments
    if re.match(r'^(https?://|www\.|[a-z]+\.ac\.|[a-z]+\.com)', tag_lower):
        return True
    return False


def _clean_skill_tags(raw_tags):
    """Deduplicate, filter noise, normalize."""
    seen = set()
    clean = []
    for tag in raw_tags:
        tag = tag.strip()
        if not tag or _is_noise(tag):
            continue
        key = tag.lower().strip()
        if key not in seen:
            seen.add(key)
            clean.append(tag)
    return clean


def _extract_skills_from_text(text):
    """Split comma/semicolon separated text into skill terms."""
    if not text:
        return []
    skills = []
    for part in re.split(r'[,;]', text):
        tag = part.strip().strip("*").strip(".")
        tag = tag.strip()
        if tag and not _is_noise(tag):
            skills.append(tag)
    return skills


# ─── Column index detection ──────────────────────────────────────────────────

def _find_columns(header_row):
    """
    Try to detect which column index corresponds to which field.
    Different coordinators may have slightly different column orders.
    Returns a dict of field_name → column_index.
    """
    mapping = {}
    for idx, cell in enumerate(header_row):
        cell_lower = cell.lower().strip()
        if "course title" in cell_lower or (cell_lower == "title"):
            mapping["title"] = idx
        elif "discipline" in cell_lower:
            mapping["discipline"] = idx
        elif "university" in cell_lower or "institute" in cell_lower or "host" in cell_lower:
            mapping["institution"] = idx
        elif "level" in cell_lower and "ncrf" not in cell_lower:
            mapping["level"] = idx
        elif "duration" in cell_lower:
            mapping["duration"] = idx
        elif "industry sector" in cell_lower or "sectors" in cell_lower:
            mapping["industry_sectors"] = idx
        elif "preview" in cell_lower and "url" in cell_lower:
            mapping["url"] = idx
        elif "language" in cell_lower and "translation" not in cell_lower and "subtitle" not in cell_lower:
            mapping["language"] = idx
        elif "program" in cell_lower and "aligned" in cell_lower:
            mapping["program"] = idx
    return mapping


def _parse_duration(duration_str):
    """Extract numeric duration in weeks from string like '12', '4.5', '12 weeks'."""
    if not duration_str:
        return None
    m = re.search(r'(\d+\.?\d*)', str(duration_str))
    if m:
        return int(float(m.group(1)))
    return None


# ─── Sheet parsing ───────────────────────────────────────────────────────────

def _parse_sheet_tab(csv_text, coordinator):
    """
    Parse a coordinator's CSV sheet tab into course dicts.
    Extracts ALL course data directly from the sheet — no preview page needed.
    """
    courses = []
    reader = csv.reader(io.StringIO(csv_text))
    rows = list(reader)

    if len(rows) < 2:
        return courses

    # Find the header row (may not be the first row — some have a title row)
    header_idx = None
    for i, row in enumerate(rows[:5]):
        row_text = " ".join(cell.lower() for cell in row)
        if "course title" in row_text or "preview" in row_text:
            header_idx = i
            break

    if header_idx is None:
        logger.debug("No header row found in %s sheet", coordinator)
        return courses

    col_map = _find_columns(rows[header_idx])
    if "title" not in col_map:
        # Try finding title by looking for "Course Title" explicitly
        for idx, cell in enumerate(rows[header_idx]):
            if "title" in cell.lower():
                col_map["title"] = idx
                break

    if "title" not in col_map:
        logger.warning("Cannot find 'title' column in %s sheet", coordinator)
        return courses

    # Parse data rows
    for row in rows[header_idx + 1:]:
        if len(row) <= col_map.get("title", 0):
            continue

        title = row[col_map["title"]].strip()
        if not title or len(title) < 3:
            continue

        # Skip non-English titles (Hindi etc.) — they won't match naukri skills
        # Allow titles with common English chars, numbers, and basic punctuation
        if not re.search(r'[a-zA-Z]', title):
            continue

        # Build course dict
        discipline = row[col_map["discipline"]].strip() if "discipline" in col_map and len(row) > col_map["discipline"] else ""
        institution = row[col_map["institution"]].strip() if "institution" in col_map and len(row) > col_map["institution"] else ""
        level = row[col_map["level"]].strip() if "level" in col_map and len(row) > col_map["level"] else ""
        duration_raw = row[col_map["duration"]].strip() if "duration" in col_map and len(row) > col_map["duration"] else ""
        industry = row[col_map["industry_sectors"]].strip() if "industry_sectors" in col_map and len(row) > col_map["industry_sectors"] else ""
        url_val = row[col_map["url"]].strip() if "url" in col_map and len(row) > col_map["url"] else ""

        # Extract URL (find the preview URL in the cell)
        url_match = re.search(r'(https://[^\s,;]+/preview)', url_val)
        if url_match:
            url_val = url_match.group(1)
        elif not url_val.startswith("http"):
            url_val = ""

        # ─── Skill Tags ─────────────────────────────────────────────────
        skill_tags = []

        # 1. Course title = primary skill
        if not _is_noise(title):
            skill_tags.append(title)

        # 2. Discipline → often meaningful (e.g. "Cyber Security", "Management")
        if discipline:
            skill_tags.extend(_extract_skills_from_text(discipline))

        # 3. Industry sectors → direct skill/domain mapping
        if industry:
            skill_tags.extend(_extract_skills_from_text(industry))

        # 4. Program aligned field sometimes has useful info
        program = row[col_map["program"]].strip() if "program" in col_map and len(row) > col_map["program"] else ""
        if program:
            skill_tags.extend(_extract_skills_from_text(program))

        skill_tags = _clean_skill_tags(skill_tags)

        course = {
            "name": title,
            "source": "SWAYAM",
            "domain": discipline if discipline and not _is_noise(discipline) else f"{coordinator} Course",
            "url": url_val,
            "institution": institution,
            "duration_weeks": _parse_duration(duration_raw),
            "difficulty": level,
            "skill_tags": skill_tags[:15],
            "syllabus_weeks": [],  # Not available from sheet data
        }
        courses.append(course)

    return courses


def scrape_swayam(max_courses=300):
    """
    Main entry point. Returns list of course dicts.

    Fetches course data from all coordinator tabs in the Google Sheet.
    No preview page scraping needed — all data comes from the sheet.
    """
    logger.info("Starting SWAYAM scrape (max=%s)", max_courses)

    all_courses = []
    for coord_name, gid in COORDINATOR_TABS.items():
        url = f"{SHEET_BASE}{gid}"
        logger.info("Fetching %s sheet tab (gid=%s)...", coord_name, gid)
        resp = _get(url)
        if not resp:
            logger.warning("Failed to fetch %s sheet tab", coord_name)
            continue

        courses = _parse_sheet_tab(resp.text, coord_name)
        logger.info("  %s: parsed %s courses from sheet", coord_name, len(courses))
        all_courses.extend(courses)

        if len(all_courses) >= max_courses:
            break

    # Deduplicate by name
    seen = set()
    unique = []
    for c in all_courses:
        key = c["name"].lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(c)

    unique = unique[:max_courses]
    logger.info("SWAYAM done: %s unique courses", len(unique))
    return unique