import pandas as pd
import re
import warnings
import os

warnings.filterwarnings('ignore')

def update_course_skills(jobs_csv_path, courses_csv_path):
    print("Loading datasets...")
    jobs_df = pd.read_csv(jobs_csv_path)
    courses_df = pd.read_csv(courses_csv_path)

    print("Extracting unique job skills...")
    unique_skills = set()
    for skills_str in jobs_df['skills'].dropna():
        for skill in str(skills_str).split(','):
            skill = skill.strip().lower()
            if len(skill) > 1 or skill in ['c', 'r', 'java', 'sql', 'css', 'html']:
                unique_skills.add(skill)

    # Sort so that longer skills are matched first (e.g. "machine learning" before "learning")
    sorted_skills = sorted(list(unique_skills), key=len, reverse=True)

    # Fallback rules for courses that don't directly name a job skill (Option D)
    fallback_rules = {
        'cyber': ['cyber security', 'information security', 'network security'],
        'eco': ['economics', 'finance', 'data analysis', 'accounting'],
        'environ': ['environmental science', 'sustainability', 'research'],
        'commerce': ['commerce', 'accounting', 'finance', 'sales'],
        'psych': ['psychology', 'counselling', 'hr', 'human resources'],
        'german': ['german', 'foreign language', 'translation', 'communication skills'],
        'animat': ['animation', 'multimedia', 'design', 'video editing'],
        'socio': ['sociology', 'social work', 'research', 'public relations'],
        'histor': ['research', 'teaching', 'content writing'],
        'art ': ['arts', 'design', 'creative'],
        'arts': ['arts', 'design', 'creative'],
        'film': ['media', 'video editing', 'production'],
        'physical educ': ['sports', 'training', 'teaching'],
        'geo': ['geography', 'gis', 'research', 'data analysis'],
        'politi': ['political science', 'public policy', 'research'],
        'litera': ['english', 'writing', 'editing', 'content writing'],
        'hindi': ['hindi', 'translation', 'content writing'],
        'bio': ['biology', 'research', 'life sciences', 'pharmaceutical'],
        'math': ['mathematics', 'statistics', 'data analysis', 'analytical skills']
    }

    updated_courses = 0
    unmatched_count = 0

    print("Updating course skills...")
    for index, row in courses_df.iterrows():
        course_name = str(row['name']).lower()
        domain = str(row['domain']).lower()
        
        course_text = f"{course_name} {domain}"
        
        matched_skills = set()
        
        # 1. Exact matching from jobs dataset
        for skill in sorted_skills:
            if len(skill) <= 4:
                # Use word boundaries for short acronyms like 'IT', 'HR', 'C++'
                pattern = r'\b' + re.escape(skill) + r'\b'
                if re.search(pattern, course_text):
                    matched_skills.add(skill.title())
            else:
                if skill in course_text:
                    matched_skills.add(skill.title())
                    
        # 2. Fallback matching for the unmatched 87 courses (Option D)
        if not matched_skills:
            for keyword, fallback_skills in fallback_rules.items():
                if keyword in course_text:
                    for fs in fallback_skills:
                        matched_skills.add(fs.title())
                    break 
                    
        # 3. Final generic fallback (if any course slips through Option D)
        if not matched_skills:
            unmatched_count += 1
            matched_skills.update(['Research', 'Communication Skills', 'Analytical Skills'])
            
        # Update specific row with comma-separated skills
        courses_df.at[index, 'skill_tags'] = ', '.join(list(matched_skills))
        updated_courses += 1

    courses_df.to_csv(courses_csv_path, index=False)
    print(f"Successfully processed {updated_courses} courses.")
    print(f"Assigned generic fallback skills to {unmatched_count} courses.")
    print(f"Updated skill tags saved to {courses_csv_path}")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    jobs_csv = os.path.join(base_dir, 'naukri_jobs.csv')
    courses_csv = os.path.join(base_dir, 'courses.csv')
    
    if os.path.exists(jobs_csv) and os.path.exists(courses_csv):
        update_course_skills(jobs_csv, courses_csv)
    else:
        print(f"Error: Could not find dataset files in {base_dir}")
