def build_search_url(role, city, page):
    role = role.replace(" ", "-")
    city = city.replace(" ", "-")
    if city.lower() == "india" or city.lower() == "all":
        if page <= 1:
            return f"https://www.naukri.com/{role}-jobs"
        return f"https://www.naukri.com/{role}-jobs-{page}"
    return f"https://www.naukri.com/{role}-jobs-in-{city}-{page}"


def build_city_search_url(city, page):
    city = city.replace(" ", "-")
    if city.lower() == "india" or city.lower() == "all":
        if page <= 1:
            return "https://www.naukri.com/jobs"
        # FIX: use the query-param URL as primary — the /jobs-N slug is a 404
        return f"https://www.naukri.com/jobs-in-india?k=jobs&l=india&pageNo={page}"
    if page <= 1:
        return f"https://www.naukri.com/jobs-in-{city}"
    return f"https://www.naukri.com/jobs-in-{city}?pageNo={page}"


def build_city_search_url_candidates(city, page):
    """
    Return candidate URLs to try in order — first match with job cards wins.

    OLD order (caused 20s timeouts):
        1. /jobs-2          ← 404 on Naukri, burns full timeout
        2. /jobs-in-india?pageNo=2  ← correct, but only tried after #1 times out
        3. /india-jobs-2    ← also 404

    NEW order (tries working URL first):
        1. /jobs-in-india?pageNo=X  ← works immediately, ~3-4s
        2. /jobs            ← page 1 fallback
        3. /india-jobs-X    ← last resort
    """
    city_slug = city.replace(" ", "-").lower()

    if city_slug == "india" or city_slug == "all":
        if page <= 1:
            # Page 1: /jobs works fine, keep it first
            return [
                "https://www.naukri.com/jobs",
                "https://www.naukri.com/jobs-in-india?k=jobs&l=india&pageNo=1",
                "https://www.naukri.com/india-jobs",
            ]
        # Pages 2+: query-param URL is the only one that works — put it first
        return [
            f"https://www.naukri.com/jobs-in-india?k=jobs&l=india&pageNo={page}",
            f"https://www.naukri.com/jobs-{page}",          # kept as fallback only
            f"https://www.naukri.com/india-jobs-{page}",    # kept as fallback only
        ]

    # Non-india cities
    if page <= 1:
        return [
            f"https://www.naukri.com/jobs-in-{city_slug}",
            f"https://www.naukri.com/jobs-in-{city_slug}?k=jobs&l={city_slug}&pageNo=1",
            f"https://www.naukri.com/{city_slug}-jobs",
        ]
    return [
        f"https://www.naukri.com/jobs-in-{city_slug}?k=jobs&l={city_slug}&pageNo={page}",
        f"https://www.naukri.com/jobs-in-{city_slug}-{page}",
        f"https://www.naukri.com/{city_slug}-jobs-{page}",
    ]