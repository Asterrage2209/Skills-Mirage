from intelligence.vulnerability_index import compute_vulnerability_index


def compute_worker_risk(profile):

    vulnerability_data = compute_vulnerability_index()

    role = profile.get("role", "").lower()
    city = profile.get("city", "")

    role_risks = vulnerability_data["role_risks"]
    region_risks = vulnerability_data["region_risks"]

    # Base risk from vulnerability model
    base_risk = role_risks.get(role, 50)

    # Region adjustment
    regional_adjust = region_risks.get(city, 0) * 0.1

    base_risk += regional_adjust

    # Experience reduction
    experience_years = profile.get("experience", 0)
    experience_reduction = min(25, experience_years * 2.5)

    # Entry level penalty
    entry_penalty = 15 if experience_years < 1 else 0

    score = base_risk - experience_reduction + entry_penalty

    score = max(5, min(95, score))

    return round(score)