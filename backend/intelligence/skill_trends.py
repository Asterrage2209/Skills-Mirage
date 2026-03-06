from collections import Counter
from data.dataset_manager import get_all_jobs

def compute_skill_trends():
    jobs = get_all_jobs()
    
    # Split jobs into older and newer halves (assuming sorted by postdate or just by index)
    # Actually dataset_manager preserves sequential index, but scraping appends to end.
    # So newer is at the end.
    midpoint = max(1, len(jobs) // 2)
    previous_group = jobs[:midpoint]
    recent_group = jobs[midpoint:]
    
    def get_counts(group):
        c = Counter()
        for j in group:
            c.update(j["skills"])
        return c
        
    prev_counts = get_counts(previous_group)
    rec_counts = get_counts(recent_group)
    
    all_skills = set(prev_counts.keys()).union(rec_counts.keys())
    trends = []
    for skill in all_skills:
        change = rec_counts.get(skill, 0) - prev_counts.get(skill, 0)
        trends.append({"skill": skill, "change": change})
        
    trends.sort(key=lambda x: x["change"], reverse=True)
    
    rising = [{"name": t["skill"], "growth": f'+{t["change"]}', "color": "from-blue-500 to-cyan-400"} for t in trends[:10] if t["change"] > 0]
    declining = [{"name": t["skill"], "decline": str(t["change"])} for t in trends[-10:] if t["change"] < 0]
    
    return {
        "rising_skills": rising,
        "declining_skills": declining
    }

