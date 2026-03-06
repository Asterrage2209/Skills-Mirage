def compute_worker_risk(profile):
    role = profile["role"]

    base_risk = 70 if "bpo" in role.lower() else 40

    experience_factor = profile["experience"] * 1.5

    score = base_risk + experience_factor

    if score > 100:
        score = 100

    return score
