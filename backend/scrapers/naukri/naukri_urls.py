def build_search_url(role, city, page):
    role = role.replace(" ", "-")
    city = city.replace(" ", "-")
    return f"https://www.naukri.com/{role}-jobs-in-{city}-{page}"


def build_city_search_url(city, page):
    city = city.replace(" ", "-")
    if page <= 1:
        return f"https://www.naukri.com/jobs-in-{city}"
    return f"https://www.naukri.com/jobs-in-{city}-{page}"


def build_city_search_url_candidates(city, page):
    city_slug = city.replace(" ", "-")
    base = build_city_search_url(city, page)
    query = f"https://www.naukri.com/jobs-in-{city_slug}?k=jobs&l={city_slug}&pageNo={page}"
    alt = f"https://www.naukri.com/{city_slug}-jobs"
    return [base, query, alt]
