import logging
import ast
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)

# Resolve dataset path relative to this file
DATASET_PATH = Path(__file__).resolve().parents[2] / "dataset" / "naukri_jobs.csv"

_jobs_df = None

def load_dataset():
    global _jobs_df
    if not DATASET_PATH.exists():
        logger.warning(f"Dataset not found at {DATASET_PATH}. Initializing empty DataFrame.")
        _jobs_df = pd.DataFrame(columns=[
            "company", "education", "experience", "industry", "jobdescription", "jobid",
            "joblocation_address", "jobtitle", "numberofpositions", "payrate", "postdate",
            "site_name", "skills", "uniq_id"
        ])
        return

    try:
        _jobs_df = pd.read_csv(DATASET_PATH, dtype=str)
        _jobs_df = _jobs_df.fillna("")
        logger.info(f"Loaded {len(_jobs_df)} jobs from dataset.")
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        _jobs_df = pd.DataFrame()

def get_all_jobs():
    if _jobs_df is None:
        load_dataset()
    if _jobs_df is None or _jobs_df.empty:
        return []

    records = _jobs_df.to_dict("records")
    ai_keywords = ["chatgpt", "openai", "generative ai", "machine learning", "automation", "llm", "gpt", "ai tools"]
    
    # Standardize dictionary for intelligence modules:
    for row in records:
        skills_str = str(row.get("skills", ""))
        if skills_str.startswith("[") and skills_str.endswith("]"):
            try:
                row["skills"] = ast.literal_eval(skills_str)
            except:
                row["skills"] = [s.strip() for s in skills_str.strip("[]").split(",") if s.strip()]
        else:
            row["skills"] = [s.strip() for s in skills_str.split(",") if s.strip()]
            
        # Map fields expected by intelligence modules
        loc = row.get("joblocation_address", "")
        row["city"] = str(loc).split(",")[0].strip() if loc else "Unknown"
        row["title"] = row.get("jobtitle", "")
        
        desc = str(row.get("jobdescription", "")).lower()
        row["ai_mentions"] = [word for word in ai_keywords if word in desc]
        
    return records

def append_jobs(new_jobs):
    global _jobs_df
    if _jobs_df is None:
        load_dataset()
        
    if not new_jobs:
        return

    new_df = pd.DataFrame(new_jobs)
    
    if "skills" in new_df.columns:
        new_df["skills"] = new_df["skills"].apply(lambda x: ",".join(x) if isinstance(x, list) else str(x))
        
    # Ensure missing schema columns are added
    for col in _jobs_df.columns:
        if col not in new_df.columns:
            new_df[col] = ""
            
    # Restrict to only the dataset fields
    new_df = new_df[_jobs_df.columns]
    
    # Handle NAs for subset
    new_df["jobtitle"] = new_df["jobtitle"].fillna("")
    new_df["company"] = new_df["company"].fillna("")
    new_df["postdate"] = new_df["postdate"].fillna("")
    
    combined = pd.concat([_jobs_df, new_df], ignore_index=True)
    
    before_len = len(_jobs_df)
    combined = combined.drop_duplicates(subset=["jobtitle", "company", "postdate"], keep="first")
    
    added = len(combined) - before_len
    if added > 0:
        _jobs_df = combined.fillna("")
        logger.info(f"Appended {added} new jobs. Resaving dataset...")
        save_dataset()

def get_latest_jobs(limit=50):
    if _jobs_df is None:
        load_dataset()
        
    if _jobs_df is None or _jobs_df.empty:
        return []
        
    # Sort by postdate
    sorted_df = _jobs_df.sort_values(by="postdate", ascending=False, na_position="last")
    top_records = sorted_df.head(limit).to_dict("records")
    
    result = []
    for row in top_records:
        loc = row.get("joblocation_address", "")
        city = str(loc).split(",")[0].strip() if loc else "Unknown"
        result.append({
            "jobtitle": row.get("jobtitle", ""),
            "company": row.get("company", ""),
            "city": city,
            "postdate": row.get("postdate", "")
        })
    return result

def save_dataset():
    if _jobs_df is not None:
        try:
            DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
            _jobs_df.to_csv(DATASET_PATH, index=False)
            logger.info(f"Saved dataset to {DATASET_PATH}")
        except Exception as e:
            logger.error(f"Failed to save dataset: {e}")

# Initialize dataset cache when module loads
load_dataset()
