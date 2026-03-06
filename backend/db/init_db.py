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
    
    # Load courses from CSV
    courses_csv_path = DATASET_DIR / "courses.csv"
    if courses_csv_path.exists():
        try:
            courses_df = pd.read_csv(courses_csv_path)
            courses_df.columns = [c.strip().lower().replace(" ", "_").replace("-", "_") for c in courses_df.columns]
            courses_df.to_sql('courses', conn, if_exists='replace', index=False)
            print(f"Loaded {len(courses_df)} courses into 'courses' table.")
        except Exception as e:
            print(f"Error loading courses.csv: {e}")
    else:
        print(f"File not found: {courses_csv_path}")

    # Load jobs from CSV
    jobs_csv_path = DATASET_DIR / "naukri_jobs.csv"
    if jobs_csv_path.exists():
        try:
            jobs_df = pd.read_csv(jobs_csv_path)
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
