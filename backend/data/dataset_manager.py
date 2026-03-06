import ast
import logging
import threading
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)

DATASET_PATH = Path(__file__).resolve().parents[2] / "dataset" / "naukri_jobs.csv"

_jobs_df = None

# RLock lets the same thread re-acquire (e.g. load_dataset called inside append_jobs)
_df_lock = threading.RLock()

_SCHEMA_COLS = [
    "company", "education", "experience", "industry", "jobdescription", "jobid",
    "joblocation_address", "jobtitle", "numberofpositions", "payrate", "postdate",
    "site_name", "skills", "uniq_id",
]

_AI_KEYWORDS = [
    "chatgpt", "openai", "generative ai", "machine learning",
    "automation", "llm", "gpt", "ai tools",
]


def load_dataset():
    global _jobs_df
    if not DATASET_PATH.exists():
        logger.warning("Dataset not found at %s. Initializing empty DataFrame.", DATASET_PATH)
        _jobs_df = pd.DataFrame(columns=_SCHEMA_COLS)
        return

    try:
        _jobs_df = pd.read_csv(DATASET_PATH, dtype=str).fillna("")
        logger.info("Loaded %s jobs from dataset.", len(_jobs_df))
    except Exception as e:
        logger.error("Failed to load dataset: %s", e)
        _jobs_df = pd.DataFrame(columns=_SCHEMA_COLS)


def _parse_skills(s):
    s = str(s)
    if s.startswith("[") and s.endswith("]"):
        try:
            return ast.literal_eval(s)
        except Exception:
            pass
    return [x.strip() for x in s.strip("[]").split(",") if x.strip()]


def get_all_jobs():
    with _df_lock:
        if _jobs_df is None:
            load_dataset()
        if _jobs_df is None or _jobs_df.empty:
            return []
        records = _jobs_df.to_dict("records")

    for row in records:
        row["skills"] = _parse_skills(row.get("skills", ""))
        loc = row.get("joblocation_address", "")
        row["city"] = str(loc).split(",")[0].strip() if loc else "Unknown"
        row["title"] = row.get("jobtitle", "")
        desc = str(row.get("jobdescription", "")).lower()
        row["ai_mentions"] = [w for w in _AI_KEYWORDS if w in desc]

    return records


def append_jobs(new_jobs):
    global _jobs_df

    with _df_lock:
        if _jobs_df is None:
            load_dataset()

        if not new_jobs:
            return

        new_df = pd.DataFrame(new_jobs)

        # Normalise field names: scraper now emits jobtitle/jobdescription/
        # joblocation_address directly; legacy scrapers emitted title/description/location.
        rename_map = {
            "title": "jobtitle",
            "description": "jobdescription",
            "location": "joblocation_address",
        }
        for old, new in rename_map.items():
            if old in new_df.columns and new not in new_df.columns:
                new_df.rename(columns={old: new}, inplace=True)

        if "skills" in new_df.columns:
            new_df["skills"] = new_df["skills"].apply(
                lambda x: ",".join(x) if isinstance(x, list) else str(x)
            )

        # Ensure all schema columns exist
        for col in _SCHEMA_COLS:
            if col not in new_df.columns:
                new_df[col] = ""

        new_df = new_df[_SCHEMA_COLS]
        new_df[["jobtitle", "company", "postdate"]] = (
            new_df[["jobtitle", "company", "postdate"]].fillna("")
        )

        combined = pd.concat([_jobs_df, new_df], ignore_index=True)
        before = len(_jobs_df)
        combined = combined.drop_duplicates(
            subset=["jobtitle", "company", "postdate"], keep="first"
        )
        added = len(combined) - before

        if added > 0:
            _jobs_df = combined.fillna("")
            logger.info("Appended %s new jobs. Saving dataset async...", added)
            _save_async(_jobs_df.copy())


def _save_async(snapshot):
    """
    Write CSV in a background daemon thread using atomic rename.
    - Writes to a .tmp file first, then os.replace() swaps it in atomically.
    - The calling thread is never blocked waiting for disk I/O.
    - If the process dies mid-write, the previous CSV is untouched.
    """
    def _write():
        try:
            DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
            tmp = DATASET_PATH.with_suffix(".tmp.csv")
            snapshot.to_csv(tmp, index=False)
            tmp.replace(DATASET_PATH)
            logger.info("Saved dataset to %s (%s rows)", DATASET_PATH, len(snapshot))
        except Exception as e:
            logger.error("Failed to save dataset: %s", e)

    threading.Thread(target=_write, daemon=True).start()


def get_latest_jobs(limit=100):
    with _df_lock:
        if _jobs_df is None:
            load_dataset()
        if _jobs_df is None or _jobs_df.empty:
            return []
        sorted_df = _jobs_df.sort_values("postdate", ascending=False, na_position="last")
        top = sorted_df.head(limit).to_dict("records")

    result = []
    for row in top:
        loc = row.get("joblocation_address", "")
        skills = row.get("skills", "")
        if isinstance(skills, list):
            skills = ", ".join(skills)
        result.append({
            "jobtitle":   row.get("jobtitle", ""),
            "company":    row.get("company", ""),
            "location":   str(loc).split(",")[0].strip() if loc else "Unknown",
            "skills":     skills,
            "experience": row.get("experience", ""),
            "postdate":   row.get("postdate", ""),
        })
    return result


def save_dataset():
    """Synchronous save — for manual/backward-compatible calls."""
    with _df_lock:
        if _jobs_df is not None:
            try:
                DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
                _jobs_df.to_csv(DATASET_PATH, index=False)
                logger.info("Saved dataset to %s", DATASET_PATH)
            except Exception as e:
                logger.error("Failed to save dataset: %s", e)


load_dataset()