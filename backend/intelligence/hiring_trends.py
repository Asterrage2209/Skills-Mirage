from collections import Counter
from data.dataset_manager import get_all_jobs

def compute_hiring_trends():
    jobs = get_all_jobs()
    month_counts = Counter()

    for job in jobs:
        postdate = str(job.get("postdate", "")).strip()
        if len(postdate) >= 7:
            # Extract YYYY-MM
            month = postdate[:7]
        else:
            month = "Unknown"
        month_counts[month] += 1

    return [{"month": m, "job_count": c} for m, c in sorted(month_counts.items())]

