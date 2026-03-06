import logging

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

CARD_SELECTORS = [
    "div.cust-job-tuple",
    "div.srp-jobtuple-wrapper",
]
DESCRIPTION_SELECTORS = [
    "span.job-desc",
    "section.job-desc",
    "div.styles_JDC__dang-inner-html",
    "div.dang-inner-html",
    "[data-testid='job-description']",
]


def extract_job_cards(html):
    soup = BeautifulSoup(html, "lxml")

    cards = []
    used_selector = None
    for selector in CARD_SELECTORS:
        cards = soup.select(selector)
        if cards:
            used_selector = selector
            break
    logger.debug("Parser found %s job cards (selector=%s)", len(cards), used_selector)

    results = []

    for c in cards:
        title = c.select_one("a.title")
        company = c.select_one("a.comp-name") or c.select_one("a.subTitle")
        location = c.select_one("span.locWdth") or c.select_one("span.loc-wrap")
        exp = c.select_one("span.expwdth") or c.select_one("span.exp-wrap")
        desc = c.select_one("span.job-desc")

        job_url = None

        if title:
            job_url = title.get("href")

        skills = [s.text.strip() for s in (c.select("li.tag-li") or c.select("li.dot"))]

        results.append(
            {
                "title": title.text.strip() if title else None,
                "company": company.text.strip() if company else None,
                "location": location.text.strip() if location else None,
                "experience": exp.text.strip() if exp else None,
                "skills": skills,
                "job_url": job_url,
                "description": desc.text.strip() if desc else None,
            }
        )

    return results


def extract_job_description(html):
    soup = BeautifulSoup(html, "lxml")

    desc = None
    selector_used = None
    for selector in DESCRIPTION_SELECTORS:
        desc = soup.select_one(selector)
        if desc:
            selector_used = selector
            break
    if not desc:
        logger.debug("No detail description found. tried selectors=%s", DESCRIPTION_SELECTORS)
    else:
        logger.debug("Detail description extracted with selector=%s", selector_used)

    if desc:
        return desc.text.strip()

    return None
