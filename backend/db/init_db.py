import json
import sqlite3
import pandas as pd
import os
from pathlib import Path

# Setup paths
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BACKEND_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
DATASET_DIR = PROJECT_DIR / "dataset"
DB_PATH = BACKEND_DIR / "db" / "chat_data.db"

def init_db():
    print(f"Initializing database at {DB_PATH}")
    os.makedirs(DB_PATH.parent, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    
    # Load courses from JSON
    courses_json_path = DATA_DIR / "courses_raw.json"
    if courses_json_path.exists():
        try:
            with open(courses_json_path, 'r', encoding='utf-8') as f:
                courses_data = json.load(f)
            if courses_data:
                courses_df = pd.DataFrame(courses_data)
                courses_df.to_sql('courses', conn, if_exists='replace', index=False)
                print(f"Loaded {len(courses_df)} courses into 'courses' table.")
        except Exception as e:
            print(f"Error loading courses.json: {e}")
    else:
        print(f"File not found: {courses_json_path}")

    # Load jobs from CSV
    jobs_csv_path = DATASET_DIR / "naukri_jobs.csv"
    if jobs_csv_path.exists():
        try:
            jobs_df = pd.read_csv(jobs_csv_path)
            # rename columns to be more SQL friendly
            jobs_df.columns = [c.strip().lower().replace(" ", "_").replace("-", "_") for c in jobs_df.columns]
            jobs_df.to_sql('jobs', conn, if_exists='replace', index=False)
            print(f"Loaded {len(jobs_df)} jobs into 'jobs' table.")
        except Exception as e:
            print(f"Error loading naukri_jobs.csv: {e}")
    else:
        print(f"File not found: {jobs_csv_path}")

    conn.close()
    print("Database initialization complete.")

if __name__ == "__main__":
    init_db()
