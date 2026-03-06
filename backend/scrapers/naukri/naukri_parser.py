import logging

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Primary card container selectors — try in order, use first that matches.
# If Naukri ever A/B-tests a new class, add it here without touching anything else.
CARD_SELECTORS = [
    "div.cust-job-tuple",
    "div.srp-jobtuple-wrapper",
    # Extended fallbacks observed on Naukri's React SPA variants:
    "article.jobTuple",
    "div[class*='jobTuple']",
    "div[class*='job-tuple']",
    "li.jobTuple",
]

DESCRIPTION_SELECTORS = [
    "span.job-desc",
    "section.job-desc",
    "div.styles_JDC__dang-inner-html",
    "div.dang-inner-html",
    "[data-testid='job-description']",
]

# Field selectors — each entry is a list of fallback selectors tried in order.
_TITLE_SELECTORS    = ["a.title", "a[title]", "h2.title", "a.jobTitle"]
_COMPANY_SELECTORS  = ["a.comp-name", "a.subTitle", "span.comp-name", "div.comp-name"]
_LOCATION_SELECTORS = ["span.locWdth", "span.loc-wrap", "span.location", "li.location"]
_EXP_SELECTORS      = ["span.expwdth", "span.exp-wrap", "span.experience", "li.experience"]
_DESC_SELECTORS     = ["span.job-desc", "div.job-desc", "p.job-desc"]
_SKILL_SELECTORS    = ["li.tag-li", "li.dot", "li.skill-li", "span.skill-tag"]


def _first(card, selectors):
    """Return the first element that matches any selector in the list."""
    for sel in selectors:
        el = card.select_one(sel)
        if el:
            return el
    return None


def _text(el):
    return el.text.strip() if el else None


def extract_job_cards(html):
    soup = BeautifulSoup(html, "lxml")

    cards = []
    used_selector = None
    for selector in CARD_SELECTORS:
        cards = soup.select(selector)
        if cards:
            used_selector = selector
            break

    logger.debug("Parser: %s cards found (selector=%s)", len(cards), used_selector)

    if not cards:
        # Emit a snippet of the HTML so we can diagnose selector drift quickly
        # without enabling full debug-HTML saving.
        preview = html[:800].replace("\n", " ").strip() if html else "<empty>"
        logger.warning(
            "extract_job_cards: 0 cards. None of %s matched. "
            "HTML preview: %s",
            CARD_SELECTORS,
            preview,
        )

    results = []
    for c in cards:
        title_el    = _first(c, _TITLE_SELECTORS)
        company_el  = _first(c, _COMPANY_SELECTORS)
        location_el = _first(c, _LOCATION_SELECTORS)
        exp_el      = _first(c, _EXP_SELECTORS)
        desc_el     = _first(c, _DESC_SELECTORS)

        job_url = title_el.get("href") if title_el else None

        # Skills: try each selector and take the union
        skills = []
        for sel in _SKILL_SELECTORS:
            found = [s.text.strip() for s in c.select(sel) if s.text.strip()]
            if found:
                skills = found
                break

        results.append({
            "jobtitle":            _text(title_el),
            "company":             _text(company_el),
            "joblocation_address": _text(location_el),
            "experience":          _text(exp_el),
            "skills":              skills,
            "job_url":             job_url,
            "jobdescription":      _text(desc_el),
            # Keep legacy keys so downstream pipeline doesn't break
            "title":               _text(title_el),
            "location":            _text(location_el),
            "description":         _text(desc_el),
        })

    return results


def extract_job_description(html):
    soup = BeautifulSoup(html, "lxml")

    for selector in DESCRIPTION_SELECTORS:
        el = soup.select_one(selector)
        if el:
            logger.debug("Detail description extracted with selector=%s", selector)
            return el.text.strip()

    logger.debug("No detail description found. tried=%s", DESCRIPTION_SELECTORS)
    return None