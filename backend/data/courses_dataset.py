"""
courses_dataset.py
------------------
Managed store for the courses dataset.
Mirrors data/dataset_manager.py in structure and patterns.

Dataset path: dataset/courses.csv  (alongside naukri_jobs.csv)
Raw JSON:     data/courses_raw.json (backup, written by courses_scraper.py)

Used by:
  - worker_engine/reskilling_engine.py  → query_courses_for_reskilling()
  - intelligence/skill_trends.py        → get_courses_for_skills() (Tab B gap map)
  - api/courses_routes.py               → REST endpoints
"""

import json
import logging
import threading
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)

DATASET_PATH = Path(__file__).resolve().parents[2] / "dataset" / "courses.csv"

_SCHEMA_COLS = [
    "name",
    "source",        # SWAYAM / NPTEL
    "domain",
    "url",
    "institution",
    "duration_weeks",
    "difficulty",
    "skill_tags",    # comma-separated string
    "syllabus_weeks", # JSON string list
]

_courses_df = None
_df_lock = threading.RLock()


# ─────────────────────────────────────────────────────────────────────────────
# Load / Save
# ─────────────────────────────────────────────────────────────────────────────

def load_dataset():
    global _courses_df
    if not DATASET_PATH.exists():
        logger.warning("Courses dataset not found at %s. Initializing empty.", DATASET_PATH)
        _courses_df = pd.DataFrame(columns=_SCHEMA_COLS)
        return

    try:
        _courses_df = pd.read_csv(DATASET_PATH, dtype=str).fillna("")
        logger.info("Loaded %s courses from dataset.", len(_courses_df))
    except Exception as e:
        logger.error("Failed to load courses dataset: %s", e)
        _courses_df = pd.DataFrame(columns=_SCHEMA_COLS)


def is_empty():
    """Returns True if no courses have been scraped yet — used for startup trigger."""
    with _df_lock:
        if _courses_df is None:
            load_dataset()
        return _courses_df is None or _courses_df.empty


def save_dataset():
    """Synchronous save — for manual/backward-compatible calls."""
    with _df_lock:
        if _courses_df is not None:
            try:
                DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
                _courses_df.to_csv(DATASET_PATH, index=False)
                logger.info("Saved courses dataset to %s", DATASET_PATH)
            except Exception as e:
                logger.error("Failed to save courses dataset: %s", e)


def _save_async(snapshot):
    """Atomic async CSV save — same pattern as dataset_manager.py."""
    def _write():
        try:
            DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
            tmp = DATASET_PATH.with_suffix(".tmp.csv")
            snapshot.to_csv(tmp, index=False)
            tmp.replace(DATASET_PATH)
            logger.info("Saved courses dataset to %s (%s rows)", DATASET_PATH, len(snapshot))
        except Exception as e:
            logger.error("Failed to save courses dataset: %s", e)

    threading.Thread(target=_write, daemon=True).start()


# ─────────────────────────────────────────────────────────────────────────────
# Write
# ─────────────────────────────────────────────────────────────────────────────

def append_courses(new_courses):
    """
    Append new courses to the dataset, deduplicating by (name, source).
    Called by courses_scraper.py after each scrape run.
    """
    global _courses_df

    with _df_lock:
        if _courses_df is None:
            load_dataset()

        if not new_courses:
            return

        new_df = pd.DataFrame(new_courses)

        # Ensure all schema columns exist
        for col in _SCHEMA_COLS:
            if col not in new_df.columns:
                new_df[col] = ""
        new_df = new_df[_SCHEMA_COLS].fillna("")

        combined = pd.concat([_courses_df, new_df], ignore_index=True)

        before = len(_courses_df)
        combined = combined.drop_duplicates(subset=["name", "source"], keep="first")
        added = len(combined) - before

        if added > 0:
            _courses_df = combined.fillna("")
            logger.info("Appended %s new courses. Saving async...", added)
            _save_async(_courses_df.copy())
        else:
            logger.info("No new courses to append (all duplicates).")


# ─────────────────────────────────────────────────────────────────────────────
# Read — used by Layer 1 (Tab B) and Layer 2 (reskilling engine)
# ─────────────────────────────────────────────────────────────────────────────

def get_all_courses():
    """Return all courses as list of dicts with parsed skill_tags and syllabus."""
    with _df_lock:
        if _courses_df is None:
            load_dataset()
        if _courses_df is None or _courses_df.empty:
            return []
        records = _courses_df.to_dict("records")

    for row in records:
        row["skill_tags"] = _parse_tags(row.get("skill_tags", ""))
        row["syllabus_weeks"] = _parse_syllabus(row.get("syllabus_weeks", ""))
        row["duration_weeks"] = _safe_int(row.get("duration_weeks"))

    return records


def query_courses_for_skills(skills, max_results=20):
    """
    Layer 1 Tab B — find courses that teach the given skills.
    Used to build the skill gap map: what's being hired vs what's being trained.

    Args:
        skills: list of skill strings (e.g. ["Python", "Machine Learning"])
        max_results: max courses to return

    Returns:
        list of course dicts ordered by relevance (tag overlap count)
    """
    all_courses = get_all_courses()
    if not all_courses or not skills:
        return []

    skill_set = {s.lower().strip() for s in skills}
    scored = []

    for course in all_courses:
        course_tags = {t.lower().strip() for t in course.get("skill_tags", [])}
        # Also search name and domain
        searchable = course_tags | {
            w.lower() for w in (course.get("name", "") + " " + course.get("domain", "")).split()
        }
        overlap = len(skill_set & searchable)
        if overlap > 0:
            scored.append((overlap, course))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:max_results]]


def query_courses_for_reskilling(target_role, current_skills, max_weeks=None, max_results=10):
    """
    Layer 2 — find courses relevant to a worker's reskilling path.

    Args:
        target_role:    string (e.g. "Data Analyst")
        current_skills: list of skills the worker already has
        max_weeks:      optional int — filter to courses ≤ this duration
        max_results:    max courses to return

    Returns:
        list of course dicts sorted by relevance, optionally filtered by duration
    """
    # Combine role keywords + skill gap as search terms
    search_terms = [w.lower() for w in target_role.split()] + [
        s.lower() for s in (current_skills or [])
    ]
    candidates = query_courses_for_skills(search_terms, max_results=50)

    # Filter by duration if requested
    if max_weeks is not None:
        candidates = [
            c for c in candidates
            if c.get("duration_weeks") is None or (c.get("duration_weeks") or 999) <= max_weeks
        ]

    return candidates[:max_results]


def get_courses_by_source(source):
    """Return all courses from a specific source (SWAYAM / NPTEL)."""
    all_courses = get_all_courses()
    return [c for c in all_courses if c.get("source", "").upper() == source.upper()]


def get_stats():
    """Return dataset stats for the /courses/stats endpoint."""
    with _df_lock:
        if _courses_df is None:
            load_dataset()
        if _courses_df is None or _courses_df.empty:
            return {"total": 0, "swayam": 0, "nptel": 0, "domains": []}

        total = len(_courses_df)
        swayam = len(_courses_df[_courses_df["source"].str.upper() == "SWAYAM"])
        nptel = len(_courses_df[_courses_df["source"].str.upper() == "NPTEL"])
        domains = _courses_df["domain"].dropna().unique().tolist()

    return {"total": total, "swayam": swayam, "nptel": nptel, "domains": domains}


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _parse_tags(tags_str):
    if not tags_str:
        return []
    return [t.strip() for t in str(tags_str).split(",") if t.strip()]


def _parse_syllabus(syllabus_str):
    if not syllabus_str:
        return []
    try:
        result = json.loads(syllabus_str)
        return result if isinstance(result, list) else []
    except Exception:
        return [s.strip() for s in str(syllabus_str).split(",") if s.strip()]


def _safe_int(val):
    try:
        return int(float(val)) if val not in (None, "", "None") else None
    except (ValueError, TypeError):
        return None


# Warm cache on import
load_dataset()