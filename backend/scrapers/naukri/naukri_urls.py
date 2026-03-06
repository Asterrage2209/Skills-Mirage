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
        return f"https://www.naukri.com/jobs-{page}"
    if page <= 1:
        return f"https://www.naukri.com/jobs-in-{city}"
    return f"https://www.naukri.com/jobs-in-{city}-{page}"


def build_city_search_url_candidates(city, page):
    city_slug = city.replace(" ", "-")
    
    if city_slug.lower() == "india" or city_slug.lower() == "all":
        base = build_city_search_url("india", page)
        query = f"https://www.naukri.com/jobs-in-india?k=jobs&l=india&pageNo={page}"
        alt = f"https://www.naukri.com/india-jobs-{page}" if page > 1 else "https://www.naukri.com/india-jobs"
        return [base, query, alt]

    base = build_city_search_url(city, page)
    query = f"https://www.naukri.com/jobs-in-{city_slug}?k=jobs&l={city_slug}&pageNo={page}"
    alt = f"https://www.naukri.com/{city_slug}-jobs"
    return [base, query, alt]
