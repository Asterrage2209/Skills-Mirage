import re
from collections import Counter
from data.dataset_manager import get_all_jobs

def compute_hiring_trends():
    jobs = get_all_jobs()
    month_counts = Counter()

    for job in jobs:
        postdate = str(job.get("postdate", "")).strip()
        month = "Recent"
        if len(postdate) >= 7:
            month_candidate = postdate[:7]
            if re.match(r'^\d{4}-\d{2}$', month_candidate):
                month = month_candidate
                
        month_counts[month] += 1

    return [{"month": m, "job_count": c} for m, c in sorted(month_counts.items())]

